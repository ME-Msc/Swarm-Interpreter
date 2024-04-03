import torch
from torch.utils.tensorboard import SummaryWriter
import numpy as np
import os
import time
from datetime import datetime
import sys
sys.path.append(os.getcwd())

from util.config import config

ACTOR_LR = config.getfloat("alg", "actor_lr")
CRITIC_LR = config.getfloat("alg", "critic_lr")
TAU = config.getfloat("alg", "tau")
STD = config.getfloat("alg", "std")
TARGET_STD = config.getfloat("alg", "target_std")
DELAY = config.getint("alg", "delay")
GAMMA = config.getfloat("alg", "gamma")
BATCH_SIZE = config.getint("alg", "batch_size")
START_UPDATE_SAMPLES = config.getint("alg", "start_update_samples")

MAIN_FOLDER =config.get("train", "main_folder") + datetime.now().strftime("%Y%m%d-%H%M%S")


class Actor(torch.nn.Module):

    def __init__(self, obs_dim, action_dim):
        super().__init__()
        self.fc0 = torch.nn.Linear(obs_dim, 64)
        self.fc1 = torch.nn.Linear(64, 64)
        self.fc2 = torch.nn.Linear(64, action_dim)

    def forward(self, x):
        x = torch.relu(self.fc0(x))
        x = torch.relu(self.fc1(x))
        a = torch.tanh(self.fc2(x))
        return a


class Critic(torch.nn.Module):

    def __init__(self, obs_dim, action_dim):
        super().__init__()
        self.fc0 = torch.nn.Linear(obs_dim + action_dim, 128)
        self.fc1 = torch.nn.Linear(128, 64)
        self.fc2 = torch.nn.Linear(64, 1)

    def forward(self, x):
        x = torch.relu(self.fc0(x))
        x = torch.relu(self.fc1(x))
        q = self.fc2(x)
        return q


class ReplayBuffer:

    def __init__(self, cap, state_dim, action_dim):
        self._states = np.zeros((cap, state_dim))
        self._actions = np.zeros((cap, action_dim))
        self._rewards = np.zeros((cap,))
        self._next_states = np.zeros((cap, state_dim))
        self._index = 0
        self._cap = cap
        self._is_full = False
        self._rnd = np.random.RandomState(19971023)

    def add(self, states, actions, rewards, next_states):
        self._states[self._index] = states
        self._actions[self._index] = actions
        self._rewards[self._index] = rewards
        self._next_states[self._index] = next_states

        self._index += 1
        if self._index == self._cap:
            self._is_full = True
            self._index = 0

    def sample(self, n):
        indices = self._rnd.randint(0, self._cap if self._is_full else self._index, (n,))
        s = self._states[indices]
        a = self._actions[indices]
        r = self._rewards[indices]
        s_ = self._next_states[indices]
        return s, a, r, s_

    def n_samples(self):
        return self._cap if self._is_full else self._index


class TD3Agent:

    def __init__(self, obs_dim, act_dim, sw=None):
        self._actor = Actor(obs_dim, act_dim)
        self._critic = [Critic(obs_dim, act_dim) for _ in range(2)]
        self._target_actor = Actor(obs_dim, act_dim)
        self._target_critic = [Critic(obs_dim, act_dim) for _ in range(2)]

        self._target_actor.load_state_dict(self._actor.state_dict())
        for i in range(2):
            self._target_critic[i].load_state_dict(self._critic[i].state_dict())

        self._actor_opt = torch.optim.Adam(self._actor.parameters(), lr=ACTOR_LR)
        self._critic_opt = [
            torch.optim.Adam(self._critic[i].parameters(), lr=CRITIC_LR) for i in range(2)
        ]

        self._act_dim = act_dim
        self._obs_dim = obs_dim
        self._sw = sw
        self._step = 0

    def soft_upd(self):
        with torch.no_grad():
            for t, s in zip(self._target_actor.parameters(), self._actor.parameters()):
                t.copy_((1 - TAU) * t.data + TAU * s.data)
            for t, s in zip(self._target_critic[0].parameters(), self._critic[0].parameters()):
                t.copy_((1 - TAU) * t.data + TAU * s.data)
            for t, s in zip(self._target_critic[1].parameters(), self._critic[1].parameters()):
                t.copy_((1 - TAU) * t.data + TAU * s.data)

    def query_target_action(self, obs):
        o = torch.tensor(obs).float()
        with torch.no_grad():
            a = self._target_actor(o)
            a = a.detach().cpu().numpy()
        target_noise = np.random.normal(0, TARGET_STD, a.shape)
        return a + target_noise

    def choose_action(self, obs):
        o = torch.tensor(np.array(obs)).float()
        with torch.no_grad():
            a = self._actor(o)
            a = a.detach().cpu().numpy()
        return a

    def choose_action_with_exploration(self, obs):
        noise = np.random.normal(0, STD, (self._act_dim,))
        a = self.choose_action(obs)
        a += noise
        return np.clip(a, -1, 1)

    def update(self, s, a, r, s_, a_):
        self._step += 1
        s_tensor = torch.tensor(s).float()
        a_tensor = torch.tensor(a).float()
        r_tensor = torch.tensor(r).float().view(-1, 1)
        next_s_tensor = torch.tensor(s_).float()
        next_a_tensor = torch.tensor(a_).float()

        if len(a_tensor.shape) == 1:
            a_tensor = a_tensor.view(-1, 1)
        if len(next_a_tensor.shape) == 1:
            next_a_tensor = next_a_tensor.view(-1, 1)

        self._actor_opt.zero_grad()
        self._critic_opt[0].zero_grad()
        self._critic_opt[1].zero_grad()

        # update critic
        next_sa_tensor = torch.cat([next_s_tensor, next_a_tensor], dim=1)
        with torch.no_grad():
            m = torch.min(self._target_critic[0](next_sa_tensor), self._target_critic[1](next_sa_tensor))
            target_q = r_tensor + GAMMA * m
        now_sa_tensor = torch.cat([s_tensor, a_tensor], dim=1)
        q_loss_log = [0, 0]
        for i in range(2):
            now_q = self._critic[i](now_sa_tensor)
            q_loss_fn = torch.nn.MSELoss()
            q_loss = q_loss_fn(now_q, target_q)
            self._critic_opt[i].zero_grad()
            q_loss.backward()
            self._critic_opt[i].step()
            q_loss_log[i] = q_loss.detach().cpu().item()

        # update actor
        a_loss_log = 0
        if self._step % DELAY == 0:
            new_a_tensor = self._actor(s_tensor)
            new_sa_tensor = torch.cat([s_tensor, new_a_tensor], dim=1)
            q = -self._critic[0](new_sa_tensor).mean()
            self._actor_opt.zero_grad()
            q.backward()
            self._actor_opt.step()
            a_loss_log = q.detach().cpu().item()
            self.soft_upd()

        if self._step % 500 == 0:
            self._sw.add_scalar('loss/critic_0', q_loss_log[0], self._step)
            self._sw.add_scalar('loss/critic_1', q_loss_log[1], self._step)
            self._sw.add_scalar('loss/actor', a_loss_log, self._step)

    def policy_state_dict(self):
        return self._actor.state_dict()

    def value_state_dict(self):
        return [self._critic[i].state_dict() for i in range(2)]
    
    def load(self, path: str):
        self._actor.load_state_dict(torch.load(path))

    def load_state_dict(self, state_dict):
        self._actor.load_state_dict(state_dict)


class TD3Trainer:

    def __init__(self, n_agents, env):
        self._n_agents = n_agents
        self._obs_dim = env.get_obs_dim()
        self._action_dim = env.get_action_dim()

        self._sw = SummaryWriter(f'./{MAIN_FOLDER}/logs/trainer')
        self._agent = TD3Agent(self._obs_dim, self._action_dim, self._sw)
        self._replay_buffer = ReplayBuffer(1000000, self._obs_dim, self._action_dim)
        self._env = env
        self._now_ep = 0
        self._step = 0

    def train_one_episode(self):
        self._now_ep += 1

        states = self._env.reset()
        done = {'__all__': False}
        total_rew = {n: 0 for n in states.keys()}

        while not done['__all__']:
            actions = {}
            in_states = []

            enum_seq = list(states.keys())
            for seq in enum_seq:
                in_states.append(states[seq])
            out_actions = self._agent.choose_action_with_exploration(in_states)
            for i, seq in enumerate(enum_seq):
                actions[seq] = out_actions[i]

            next_states, rewards, done, info = self._env.step(actions)
            self._step += 1

            for buffer_name in states.keys():
                self._replay_buffer.add(states[buffer_name], actions[buffer_name], rewards[buffer_name], next_states[buffer_name])

            if self._step % 20 == 0 and self._replay_buffer.n_samples() > START_UPDATE_SAMPLES:
                for _ in range(20):
                    s, a, r, s_ = self._replay_buffer.sample(BATCH_SIZE)
                    a_ = self._agent.query_target_action(s_)
                    self._agent.update(s, a, r, s_, a_)

            for seq in enum_seq:
                total_rew[seq] += rewards[seq]
            states = next_states
            for k, v in done.items():
                if v and k != '__all__':
                    del states[k]
        if self._now_ep % 200 == 0:
            self._sw.add_scalar(f'train_rew/0', total_rew['uav_0'], self._now_ep)
        return total_rew

    def test_one_episode(self):
        states = self._env.reset()
        done = {'__all__': False}
        total_rew = {n: 0 for n in states.keys()}

        while not done['__all__']:
            actions = {}
            in_states = []
            enum_seq = list(states.keys())
            for seq in enum_seq:
                in_states.append(states[seq])
            out_actions = self._agent.choose_action(in_states)
            for i, seq in enumerate(enum_seq):
                actions[seq] = out_actions[i]

            next_states, rewards, done, info = self._env.step(actions)

            for seq in enum_seq:
                total_rew[seq] += rewards[seq]
            states = next_states

            for k, v in done.items():
                if v and k != '__all__':
                    del states[k]
            
        for i in range(self._n_agents):
            self._sw.add_scalar(f'test_rew/{i}', total_rew[f'uav_{i}'], self._now_ep)
        return total_rew

    def save(self):
        path = f'./{MAIN_FOLDER}/models'
        if not os.path.exists(path):
            os.makedirs(path)
        save_pth = path + '/' + f'{self._now_ep}.pkl'
        torch.save(self._agent.policy_state_dict(), save_pth)
