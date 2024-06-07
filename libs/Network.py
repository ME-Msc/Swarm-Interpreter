import os

from libs.RL.td3 import TD3Agent

agent = TD3Agent(3, 1)
current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)
agent.load(current_directory+"/RL/fly_circle.pkl")


def one_round(getState_func, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	circle_center = kwargs["circle_center"]
	radius = kwargs["radius"]
	start_position = kwargs["start_position"]
	agent = kwargs["circle_agent"]
	client = kwargs["wrapper"].clients[vehicle_name]

	import math
	import numpy as np
	step_count = 0
	while True:
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
		client.moveByVelocityZAsync(vx=new_vx, vy=new_vy, z=hover_z, duration=1, vehicle_name=vehicle_name)

		distance_to_start_position = math.sqrt((state.kinematics_estimated.position.x_val - start_position.position.x_val)**2 + (state.kinematics_estimated.position.y_val - start_position.position.y_val)**2)

		if (distance_to_start_position < 0.1 *radius and step_count >= 1000) or step_count > 10000:
			break

		step_count += 1




TD3_fly_circle = agent

TD3_fly_circle.one_round = one_round