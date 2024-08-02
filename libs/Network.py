import os
import threading
import numpy as np

from libs.RL.td3 import TD3Agent
from libs.RL.dqn import DQNAgent

current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)

def fly_circle_one_round(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	getState_func = kwargs["getState_func"]
	circle_center = kwargs["circle_center"]
	radius = kwargs["radius"]
	start_position = kwargs["start_position"]
	agent:TD3Agent = kwargs["circle_agent"]
	client = kwargs["wrapper"].clients[vehicle_name]
	Lock = kwargs["wrapper"].locks[vehicle_name]
	Behaviors_or_Tasks = kwargs["goal_caller"][0]
	Behavior_or_Task_name = kwargs["goal_caller"][1]
	my_goal_reached:threading.Event = kwargs["goal_reached"][Behaviors_or_Tasks][Behavior_or_Task_name][vehicle_name]

	import math
	import numpy as np
	step_count = 0
	while not my_goal_reached.is_set():
		state = getState_func(**kwargs)
		vx = state.kinematics_estimated.linear_velocity.x_val
		vy = state.kinematics_estimated.linear_velocity.y_val
		theta = math.atan2(vy, vx)
		flyCircle_state = np.array([(state.kinematics_estimated.position.x_val - circle_center[0]) / radius, 
									(state.kinematics_estimated.position.y_val - circle_center[1]) / radius, theta], dtype=np.float32)

		action = agent.choose_action(flyCircle_state)
		# LogLock.acquire()
		# print(f"state = {flyCircle_state}, action = {action}")
		# LogLock.release()
		new_vx = math.cos(theta + action[0]) * radius / 2
		new_vy = math.sin(theta + action[0]) * radius / 2
		# new_v = math.sqrt(new_vx**2 + new_vy**2)
		hover_z = state.kinematics_estimated.position.z_val
		# new_x = state.kinematics_estimated.position.x_val + new_vx * 0.1
		# new_y = state.kinematics_estimated.position.y_val + new_vy * 0.1
		# client.moveToPositionAsync(x=new_x, y=new_y, z=hover_z, velocity=new_v, vehicle_name=vehicle_name)
		Lock.acquire()
		client.moveByVelocityZAsync(vx=new_vx, vy=new_vy, z=hover_z, duration=1, vehicle_name=vehicle_name)
		Lock.release()

		distance_to_start_position = math.sqrt((state.kinematics_estimated.position.x_val - start_position[0])**2 + (state.kinematics_estimated.position.y_val - start_position[1])**2)

		if (distance_to_start_position < 0.1 *radius and step_count >= 1000) or step_count > 5000:
			break

		step_count += 1


TD3_fly_circle = TD3Agent(3, 1)
TD3_fly_circle.load(current_directory+"/RL/fly_circle.pkl")
TD3_fly_circle.one_round = fly_circle_one_round


def cnnRecognize(*swarm_args, **kwargs):
	import random
	weights = [0.3, 0.7]  # 设置权重，对应 True 和 False 的概率
	options = [True, False]
	res = random.choices(options, weights, k=1)[0]
	import datetime
	print(str(datetime.datetime.now()) + " " + str(res))
	return res

class Cover_Env():
	def __init__(self) -> None:
		self.uav_pos = {}
		self.cover_map = np.zeros((10, 10), dtype=np.int32)

	def set_scale(self, scale):
		self.scale = scale

	def update(self, uav_name, x, y):
		self.uav_pos[uav_name] = (x, y)
		self.cover_map[x][y] = 1

	def get_obs(self, uav_name):
		one_hot_position = np.zeros((10, 2), dtype=np.int32)
		x = int(self.uav_pos[uav_name][0])
		y = int(self.uav_pos[uav_name][1])
		one_hot_position[x][0] = 1
		one_hot_position[y][1] = 1
		obs = np.concatenate([self.cover_map, one_hot_position], axis=1).reshape(1, -1)
		return obs
	
	def get_done(self):
		return np.all(self.cover_map == 1)


def cover_one_round(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	getPosition_func = kwargs["getPosition_func"]
	flyTo_func = kwargs["flyTo_func"]
	agent:DQNAgent = kwargs["cover_agent"]
	scale = kwargs['scale']
	env:Cover_Env = DQN_cover.env
	env.set_scale(scale=scale)
	client = kwargs["wrapper"].clients[vehicle_name]
	Lock = kwargs["wrapper"].locks[vehicle_name]
	Behaviors_or_Tasks = kwargs["goal_caller"][0]
	Behavior_or_Task_name = kwargs["goal_caller"][1]
	my_goal_reached:threading.Event = kwargs["goal_reached"][Behaviors_or_Tasks][Behavior_or_Task_name][vehicle_name]

	done = False
	while not my_goal_reached.is_set() and not done:
	# while not done:
		pos = getPosition_func(**kwargs)
		env.update(uav_name=vehicle_name, x=round(pos[0]/scale), y=round(pos[1]/scale))
		cover_obs = env.get_obs(uav_name=vehicle_name)
		action = agent.choose_action(state=cover_obs, epsilon=0.1)
		dxy = np.array([
            [0, 1],
            [0, -1],
            [1, 0],
            [-1, 0]
        ])
		target_x = int(round(pos[0]/scale) + dxy[action][0])
		target_y = int(round(pos[1]/scale) + dxy[action][1])
		target_x = int(np.clip(target_x, 0, 9)) * scale
		target_y = int(np.clip(target_y, 0, 9)) * scale
		target_xyz = (target_x, target_y, pos[2])
		flyTo_func(target_xyz, **kwargs)
		done = env.get_done()


DQN_cover = DQNAgent(120, 4)
DQN_cover.load(current_directory+"/RL/cover_10_10_2.pkl")
DQN_cover.env = Cover_Env()
DQN_cover.one_round = cover_one_round