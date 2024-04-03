import time
import numpy as np
from util.config import config
from env.trees_go_env import TreesGoEnv
from algorithm.td3 import TD3Agent

VELOCITY = config.getfloat("uav", "velocity")
MAX_DA = config.getfloat("uav", "max_da")
MAX_DZ = config.getfloat("uav", "max_dz")
DT = config.getfloat("uav", "dt")


class SimUav:
    
    def __init__(self, id, home) -> None:
        self.id = id
        self.pos = np.zeros(3, dtype=np.float32)
        self.theta = np.zeros(1, dtype=np.float32)
        self.home = np.array(home)

    def reset(self):
        self.pos = np.zeros(3, dtype=np.float32)
        self.pos[:2] = self.home[:2]
        self.theta = np.random.uniform(-np.pi * 3 / 4, -np.pi / 4)

    def set_world(self, world):
        self.world = world

    def set_state(self, state):
        self.pos = state['pos'].copy()
        self.theta = state['theta']

    def get_state(self):
        state = {}
        state['pos'] = self.pos.copy()
        state['theta'] = self.theta
        return state

    def take_action(self, obs, action):
        self.theta += action[0] * MAX_DA * DT

        if self.theta > np.pi:
            self.theta -= 2 * np.pi
        if self.theta < -np.pi:
            self.theta += 2 * np.pi
        
        self.pos[0] += VELOCITY * np.cos(self.theta) * DT
        self.pos[1] += VELOCITY * np.sin(self.theta) * DT
        self.pos[2] += action[1] * MAX_DZ * DT

    def trees_go_RPC_call(self):
        env = TreesGoEnv(uav=self)

        td3agent = TD3Agent(obs_dim=env.get_obs_dim(), act_dim=env.get_action_dim())
        td3agent.load(config.get("evaluate", "model_path"))

        state = env.reset(mode="evaluate")
        # input("Press Enter to start...")
        while not env._done:
            # with self.world.lock:
            #     self.world.render()
            self.world.update_state()
            time.sleep(.1)
            action = td3agent.choose_action(state)
            next_state, reward, done, info = env.step(action)
            state = next_state
            env._done = done
