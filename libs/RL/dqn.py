import os
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.tensorboard import SummaryWriter


class QNet(nn.Module):

    def __init__(self, state_dim, action_cnt):
        super().__init__()
        self.fc0 = nn.Linear(state_dim, 256)
        self.fc1 = nn.Linear(256, 256)
        self.fc2 = nn.Linear(256, action_cnt)

    def forward(self, x):
        x = torch.relu(self.fc0(x))
        x = torch.relu(self.fc1(x))
        q = self.fc2(x)
        return q
    

class ReplyBuffer1D1D:

    def __init__(self, capacity, state_dim):
        self._states = np.zeros((capacity, state_dim), dtype=np.float32)
        self._actions = np.zeros((capacity, ), dtype=np.uint8)
        self._rewards = np.zeros((capacity, ), dtype=np.float32)
        self._next_states = np.zeros((capacity, state_dim), dtype=np.float32)
        self._done = np.zeros((capacity, ), dtype=np.bool_)

        self._full = False
        self._idx = 0
        self._capacity = capacity

    def add(self, state, action, reward, next_state, done):
        self._states[self._idx, :] = state
        self._actions[self._idx] = action
        self._rewards[self._idx] = reward
        self._next_states[self._idx, :] = next_state
        self._done[self._idx] = done

        self._idx += 1
        if self._idx == self._capacity:
            self._full = True
            self._idx = 0

    def sample(self, n):
        indices = np.random.randint(0, self._capacity if self._full else self._idx, (n, ))
        s, a, r, s_, d = self._states[indices], self._actions[indices], self._rewards[indices], self._next_states[indices], self._done[indices]
        return s, a, r, s_, d
    
    def n_samples(self):
        return self._capacity if self._full else self._idx


class DQNAgent:

    def __init__(self, obs_dim=120, act_dim=4):
        self.tau = 64
        self.gamma = 0.95
        self.lr = 1e-4
        self.step = 0
        self.obs_dim = obs_dim
        self.act_cnt = act_dim
        self.qnet = QNet(self.obs_dim, self.act_cnt)
        self.target_qnet = QNet(self.obs_dim, self.act_cnt)
        self.target_qnet.load_state_dict(self.qnet.state_dict())
        self.opt = optim.Adam(self.qnet.parameters(), lr=self.lr)

    def choose_action(self, state, epsilon):
        if epsilon != 0 and np.random.uniform() < epsilon:
            # sample n actions
            return np.random.randint(0, self.act_cnt)
        s = torch.from_numpy(state).float()
        with torch.no_grad():
            q = self.qnet(s)
            opt_a = torch.argmax(q, -1)

        res = opt_a.numpy()
        return res.squeeze()
    
    def update(self, s, a, r, s_, d):
        s_tensor = torch.tensor(s)
        a_tensor = torch.tensor(a).long()
        r_tensor = torch.tensor(r)
        ns_tensor = torch.tensor(s_)
        d_tensor = torch.tensor(d).float()

        with torch.no_grad():
            next_target_v = self.target_qnet(ns_tensor)
            next_v = self.qnet(ns_tensor)
            next_a = torch.argmax(next_v, dim=-1, keepdim=True)
            next_q = next_target_v.gather(-1, next_a).view(-1)
            targets = r_tensor + self.gamma * next_q * (1 - d_tensor)

        v = self.qnet(s_tensor)
        q = v.gather(-1, a_tensor.view(-1, 1)).view(-1)
        loss_fn = nn.MSELoss()

        loss = loss_fn(q, targets)
        self.opt.zero_grad()
        loss.backward()
        self.opt.step()

        self.step += 1

        if self.step % self.tau == 0:
            self.target_qnet.load_state_dict(self.qnet.state_dict())

        return {
            'td_error': loss.detach().item()
        }
    
    def load(self, path: str):
        self.qnet.load_state_dict(torch.load(path))
    

class DQNTrainer:

    def __init__(self, env_creator, env_config, algo_config) -> None:
        self.env = env_creator(env_config)

        self.obs_dim = self.env.observation_space.shape[0] * self.env.observation_space.shape[1]

        self.agent = DQNAgent(self.env, algo_config)
        self.buffer = ReplyBuffer1D1D(algo_config['buffer'], self.obs_dim)  # TODO: fixit

        self.warm_up = algo_config['warm_up']
        self.upd_cnt = algo_config['upd_cnt']
        self.batch_size = algo_config['batch_size']
        self.epsilon = algo_config['epsilon']
        self.log_dir = algo_config['log_dir']

        self._episode = 0
        self._sw = SummaryWriter(self.log_dir)

        if not os.path.exists(os.path.join(self.log_dir, 'models')):
            os.makedirs(os.path.join(self.log_dir, 'models'))

    def _update(self):
        td_error = 0
        if self.buffer.n_samples() > self.warm_up:
            for _ in range(self.upd_cnt):
                s, a, r, s_, d = self.buffer.sample(self.batch_size)
                log = self.agent.update(s, a, r, s_, d)
                td_error += log['td_error']
        return td_error / self.upd_cnt

    def train_one_episode(self):
        s, info = self.env.reset()
        done = {'__all__': False}
        total = 0

        s_tr_prev = {}
        a_tr_prev = {}

        td_error = []
        while not done['__all__']:
            acts = {}
            for k, v in s.items():
                a = self.agent.choose_action(v, self.epsilon)
                acts[k] = a
            
            s_tr_prev.update(s)
            a_tr_prev.update(acts)

            s_, r, done, truncateds, info = self.env.step(acts)
            # total += np.mean(list(r.values()))

            for k in s_.keys():
                self.buffer.add(s_tr_prev[k], a_tr_prev[k], r[k], s_[k], done[k] and not truncateds[k])
            s = s_

            upd_logs = self._update()
            td_error.append(upd_logs)
        self._episode += 1
        
        total = self.env.get_score()

        if self._episode % 1 == 0:
            self._sw.add_scalar('rew', total, self._episode)
            self._sw.add_scalar('td', np.mean(td_error), self._episode)
            td_error.clear()

        return {
            'total_mean_rewards': total
        }
    
    def eval_one_episode(self):
        s, info = self.env.reset()
        done = {'__all__': False}
        total = 0


        while not done['__all__']:
            acts = {}
            for k, v in s.items():
                a = self.agent.choose_action(v, 0)
                acts[k] = a
            s_, r, done, truncateds, info = self.env.step(acts)
           
            s = s_
        self._sw.add_scalar('rew-eval', total, self._episode)
        # self._sw.add_scalar('coverage', self.env.grid_vis_map.sum(), self._episode)

        total = self.env.get_score()
        return {
            'total_mean_rewards': total
        }

    def save(self):
        p = self.agent.qnet.state_dict()
        pth = os.path.join(self.log_dir, 'models')
        torch.save(p, f'{pth}/{self._episode}')
