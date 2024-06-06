import math
import threading
import time
import copy
import airsim
import os
from interpreter.rpc.searchTspSolver import searchTspSolver

LogLock = threading.Lock()


class AirsimWrapper:
	# Basic
	def __init__(self, wait_or_not=True):
		# connect to the AirSim simulator
		self.clients = {}
		self.home = {}
		self.lock = threading.Lock()
		self.task = {}
		self.behavior = {}

		if wait_or_not:
			# set_global_camera
			client = airsim.MultirotorClient()
			self.clients["GlobalCamera"] = client
			self.clients["GlobalCamera"].confirmConnection()
			self.clients["GlobalCamera"].enableApiControl(True)
			self.clients["GlobalCamera"].takeoffAsync().join()
			self.clients["GlobalCamera"].moveToPositionAsync(0, 0, -100, 10).join()
			self.clients["GlobalCamera"].hoverAsync().join()

			message = (
				"1. Push / to switch to chase with spring arm mode.\n"
				"2. Wait for the drone to fly to an altitude of 300 meters.\n"
				"3. Push M to switch to manual camera control.\n"
				"4. Push S to move the view downwards, regard the drone as a global camera.\n"
				"5. Press any key to continue after the global camera is ready."
			)
			airsim.wait_key(message=message)

	def copy(self):
		new_wrapper = AirsimWrapper(wait_or_not=False)
		for k, v in self.clients.items():
			if k != "GlobalCamera":
				new_wrapper.clients[k] = self.clients[k]
		new_wrapper.home = copy.deepcopy(self.home)
		new_wrapper.lock = threading.Lock()
		new_wrapper.task = copy.deepcopy(self.task)
		return new_wrapper

	def set_home(self, agents_list: list):
		group = len(self.home)
		for i in range(len(agents_list)):
			client = airsim.MultirotorClient()
			vhcl_nm = agents_list[i]
			self.clients[vhcl_nm] = client

			pose = airsim.Pose(airsim.Vector3r(group, i * 2, 0), airsim.to_quaternion(0, 0, 0))
			self.home[vhcl_nm] = pose

			client.simAddVehicle(vhcl_nm, "simpleflight", pose)
			client.enableApiControl(True, vhcl_nm)
			client.armDisarm(True, vhcl_nm)
			client.simSetTraceLine(color_rgba=[1.0, 0, 0, 0], thickness=20.0, vehicle_name=vhcl_nm)
		time.sleep(2)

	# RPC
	def takeOff_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]

		res = client.takeoffAsync(vehicle_name=vehicle_name)
		self.lock.acquire()
		res.join()
		self.lock.release()


	def flyToHeight_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]

		pose = client.simGetVehiclePose(vehicle_name=vehicle_name)
		res = client.moveToPositionAsync(pose.position.x_val, pose.position.y_val, -rpc_args[0], 10, vehicle_name=vehicle_name)

		self.lock.acquire()
		res.join()
		self.lock.release()


	def getPosition_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		pos = client.simGetVehiclePose(vehicle_name=vehicle_name)
		pos.position.x_val += self.home[vehicle_name].position.x_val
		pos.position.y_val += self.home[vehicle_name].position.y_val
		pos.position.z_val += self.home[vehicle_name].position.z_val 
		return (pos.position.x_val, pos.position.y_val, pos.position.z_val)


	def getState_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		state:airsim.MultirotorState = client.getMultirotorState(vehicle_name=vehicle_name)

		state.kinematics_estimated.position.x_val += self.home[vehicle_name].position.x_val
		state.kinematics_estimated.position.y_val += self.home[vehicle_name].position.y_val
		state.kinematics_estimated.position.z_val += self.home[vehicle_name].position.z_val 
		return state


	def getDestination_API(self, *rpc_args, vehicle_name):
		mapper = {
			"search_uav_0": 0,
			"search_uav_1": 1,
			"search_uav_2": 2
		}
		index = mapper[vehicle_name]
		traces = rpc_args[0][index]
		pos = rpc_args[1]
		
		min_distance = float('inf')
		closest_index = -1
		dest = traces[closest_index]
		
		# Calculate the distance from pos to each point in traces
		for i, (x, y) in enumerate(traces):
			distance = math.sqrt((x - pos[0])**2 + (y - pos[1])**2)
			if distance < min_distance:
				min_distance = distance
				closest_index = i
		
		# If the closest point is the last point in traces, return it
		if closest_index == len(traces) - 1:
			dest = traces[closest_index]
		else:
			# Otherwise, return the next point in traces
			dest = traces[closest_index + 1]
		return (dest[0], dest[1], pos[2]) 


	def flyTo_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		destination = rpc_args[0]	# World coordinate system

		# Relative coordinate system
		relative_destination_x = destination[0] - self.home[vehicle_name].position.x_val
		relative_destination_y = destination[1] - self.home[vehicle_name].position.y_val
		relative_destination_z = destination[2] - self.home[vehicle_name].position.z_val

		res = client.moveToPositionAsync(relative_destination_x, relative_destination_y, relative_destination_z, 2, vehicle_name=vehicle_name)
		self.lock.acquire()
		res.join()
		self.lock.release()


	def flyCircle_v0_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		state = rpc_args[0]
		radius = rpc_args[1]

		import math
		start_position = self.behavior["flyCircle"]["start_position_on_circle"][vehicle_name]
		circle_center = (round(start_position.position.x_val), round(start_position.position.y_val) + radius)
		vx = state.kinematics_estimated.linear_velocity.x_val / radius
		vy = state.kinematics_estimated.linear_velocity.y_val / radius
		theta = math.atan2(vy, vx)
		
		import numpy as np
		flyCircle_state = np.array([(start_position.position.x_val - circle_center[0]) / radius, 
							  		(start_position.position.y_val - circle_center[1]) / radius, 0], dtype=np.float32)
		agent = self.behavior["flyCircle"]["agent"]
		action = agent.choose_action(flyCircle_state)
		new_vx = math.cos(theta + action[0]) * radius / 2
		new_vy = math.sin(theta + action[0]) * radius / 2
		hover_z = state.kinematics_estimated.position.z_val
		client.moveByVelocityZAsync(vx=new_vx, vy=new_vy, z=hover_z, duration=1, vehicle_name=vehicle_name)


	def flyCircle_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		TD3agent = rpc_args[0]
		radius = rpc_args[1]
		
		start_position = self.behavior["flyCircle"]["start_position_on_circle"][vehicle_name]
		circle_center = (round(start_position.position.x_val), round(start_position.position.y_val) + radius)
		LogLock.acquire()
		print(f"vehicle_name = {vehicle_name}, start = {start_position}, center = {circle_center}")
		LogLock.release()

		import math
		import numpy as np
		step_count = 0
		while True:
			state = self.getState_API(vehicle_name=vehicle_name)
			vx = state.kinematics_estimated.linear_velocity.x_val
			vy = state.kinematics_estimated.linear_velocity.y_val
			theta = math.atan2(vy, vx)
			flyCircle_state = np.array([(state.kinematics_estimated.position.x_val - circle_center[0]) / radius, 
										(state.kinematics_estimated.position.y_val - circle_center[1]) / radius, theta], dtype=np.float32)

			action = TD3agent.choose_action(flyCircle_state)
			LogLock.acquire()
			print(f"state = {flyCircle_state}, action = {action}")
			LogLock.release()
			new_vx = math.cos(theta + action[0]) * radius / 2
			new_vy = math.sin(theta + action[0]) * radius / 2
			new_v = math.sqrt(new_vx**2 + new_vy**2)
			hover_z = state.kinematics_estimated.position.z_val
			# new_x = state.kinematics_estimated.position.x_val + new_vx * 0.1
			# new_y = state.kinematics_estimated.position.y_val + new_vy * 0.1
			# client.moveToPositionAsync(x=new_x, y=new_y, z=hover_z, velocity=new_v, vehicle_name=vehicle_name)
			client.moveByVelocityZAsync(vx=new_vx, vy=new_vy, z=hover_z, duration=1, vehicle_name=vehicle_name)

			distance_to_start_position = math.sqrt((state.kinematics_estimated.position.x_val - start_position.position.x_val)**2 + (state.kinematics_estimated.position.y_val - start_position.position.y_val)**2)

			if (distance_to_start_position < 0.1 *radius and step_count >= 1000) or step_count > 50000:
				break

			step_count += 1


	# Behaviors
	def cover_Behavior(self, *rpc_args, vehicle_name):
		pass

	def takeOff_Behavior(self, *rpc_args, vehicle_name):
		pass

	def flyCircle_Behavior(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		if "flyCircle" not in self.behavior:
			self.behavior["flyCircle"] = {}

		if "start_position_on_circle" not in self.behavior["flyCircle"]:
			# A dictionary of start position on circle of different vehicles
			# the key is vehicle name, the value is a relative position of the home of this vehicle
			# Only keep the start_position_on_circle rather than circle_center
			# because circle_center is depend on radius which can not be known while setting the environment of flyCircle_Behavior
			self.behavior["flyCircle"]["start_position_on_circle"] = {}
		self.behavior["flyCircle"]["start_position_on_circle"][vehicle_name] = client.simGetVehiclePose(vehicle_name=vehicle_name)	# relative position of the home of vehicle


	# Tasks
	def search(self, vehicle_name_list):
		pass

	"""
	AirSimWrapper封装了两类实体
	1. 真实世界的虚拟仿真（简称为world）
	2. 无人机的所有状态和运动控制
	3. 任务相关的其他信息

	我们提供AirsimWrapper给用户使用，用户可以调用AirSimWrapper提供的接口
	要求Airsim提供以下服务：
	1. 无人机的位置
	2. 物理世界的现状
	3. 无人机的控制
	4. 其他任务相关的信息获取和状态修改
	
	"""