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
			self.clients["GlobalCamera"].moveToPositionAsync(0, 0, -120, 10).join()
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


	def getState_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		state:airsim.MultirotorState = client.getMultirotorState(vehicle_name=vehicle_name)

		state.kinematics_estimated.position.x_val += self.home[vehicle_name].position.x_val
		state.kinematics_estimated.position.y_val += self.home[vehicle_name].position.y_val
		state.kinematics_estimated.position.z_val += self.home[vehicle_name].position.z_val 
		return state


	def getTspDestination_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		state:airsim.MultirotorState = rpc_args[0]

		position = state.kinematics_estimated.position
		task = self.task["search"]
		vehicle_id = task.id[vehicle_name]
		search_task_next_step = task.get_i_vehicle_next_step_location(vehicle_id, position.x_val, position.y_val)
		destination = copy.deepcopy(position)
		destination.x_val = search_task_next_step[0]
		destination.y_val = search_task_next_step[1]
		destination.z_val = round(destination.z_val)
		
		return destination


	def flyTo_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		destination = rpc_args[0]	# World coordinate system
		
		# LogLock.acquire()
		# print(f'!!!!! {vehicle_name}, id={id(vehicle_name)}\n!!!!! destination = {destination}\n')
		# LogLock.release()

		# Relative coordinate system
		relative_destination_x = destination.x_val - self.home[vehicle_name].position.x_val
		relative_destination_y = destination.y_val - self.home[vehicle_name].position.y_val
		relative_destination_z = destination.z_val - self.home[vehicle_name].position.z_val

		res = client.moveToPositionAsync(relative_destination_x, relative_destination_y, relative_destination_z, 2, vehicle_name=vehicle_name)
		self.lock.acquire()
		res.join()
		self.lock.release()


	def flyCircle_API(self, *rpc_args, vehicle_name):
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


	# Behaviors
	def search_Behavior(self, *rpc_args, vehicle_name):
		pass

	def takeOff_Behavior(self, *rpc_args, vehicle_name):
		pass

	def flyCircle_Behavior(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		if "flyCircle" not in self.behavior:
			self.behavior["flyCircle"] = {}

		from interpreter.rpc.RL.td3 import TD3Agent
		agent = TD3Agent(3, 1)
		current_file_path = os.path.abspath(__file__)
		current_directory = os.path.dirname(current_file_path)
		agent.load(current_directory+"/RL/fly_circle.pkl")
		self.behavior["flyCircle"]["agent"] = agent

		
		if "start_position_on_circle" not in self.behavior["flyCircle"]:
			# A dictionary of start position on circle of different vehicles
			# the key is vehicle name, the value is a relative position of the home of this vehicle
			# Only keep the start_position_on_circle rather than circle_center
			# because circle_center is depend on radius which can not be known while setting the environment of flyCircle_Behavior
			self.behavior["flyCircle"]["start_position_on_circle"] = {}
		self.behavior["flyCircle"]["start_position_on_circle"][vehicle_name] = client.simGetVehiclePose(vehicle_name=vehicle_name)	# relative position of the home of vehicle


	# Tasks
	def search(self, vehicle_name_list):
		search_home = {}
		for vhcl_nm in vehicle_name_list:
			if vhcl_nm in self.home:
				position = self.home[vhcl_nm].position
				x = position.x_val
				y = position.y_val
				search_home[vhcl_nm] = (x, y)
		self.task["search"] = searchTspSolver(0, 20, 10, search_home)
		self.task["search"].print_solution()

