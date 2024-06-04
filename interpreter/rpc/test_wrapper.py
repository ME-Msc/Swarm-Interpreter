import math
import threading
import time
import copy
import airsim
import os
from interpreter.rpc.searchTspSolver import searchTspSolver

LogLock = threading.Lock()


class TestWrapper:
	# Basic
	def __init__(self, wait_or_not=True):
		# simulation of AirSim
		self.clients = {}
		self.locations = {}
		self.home = {}
		self.lock = threading.Lock()
		self.task = {}
		self.behavior = {}

	def copy(self):
		new_wrapper = TestWrapper(wait_or_not=False)
		for k, v in self.clients.items():
			if k != "GlobalCamera":
				new_wrapper.clients[k] = self.clients[k]
		new_wrapper.locations = copy.deepcopy(self.locations)
		new_wrapper.home = copy.deepcopy(self.home)
		new_wrapper.lock = threading.Lock()
		new_wrapper.task = copy.deepcopy(self.task)
		new_wrapper.behavior = copy.deepcopy(self.behavior)
		return new_wrapper

	def set_home(self, agents_list: list):
		LogLock.acquire()
		print("set_home : ", agents_list)
		LogLock.release()
		for agent in agents_list:
			self.home[agent] = (0, len(self.home)*2)
			self.locations[agent] = (0, len(self.locations)*2, 0)

	# RPC
	def takeOff_API(self, *rpc_args, vehicle_name):
		x, y, z = self.locations[vehicle_name]
		self.locations[vehicle_name] = (x, y, 2)
		LogLock.acquire()
		print(f"takeOff_API : {vehicle_name}, ({x}, {y}, 2)")
		LogLock.release()

	def flyToHeight_API(self, *rpc_args, vehicle_name):
		x, y, z = self.locations[vehicle_name]
		self.locations[vehicle_name] = (x, y, rpc_args[0])
		LogLock.acquire()
		print(f"flyToHeight_API : {vehicle_name}, ({x}, {y}, {rpc_args[0]})")
		LogLock.release()

	def flyTo_API(self, *rpc_args, vehicle_name):
		x, y, z = self.locations[vehicle_name]
		tar_x, tar_y = rpc_args[0][0], rpc_args[0][1]
		self.locations[vehicle_name] = (tar_x, tar_y, z)
		LogLock.acquire()
		print(f"flyTo_API : {vehicle_name}, ({x}, {y}, {z})->({tar_x}, {tar_y}, {z})")
		LogLock.release()

	def flyCircle_API(self, *rpc_args, vehicle_name):
		LogLock.acquire()
		print(f"flyCircle_API : {vehicle_name}, radius = {rpc_args[1]})")
		LogLock.release()

	def getPosition_API(self, *rpc_args, vehicle_name):
		x, y, z = self.locations[vehicle_name]
		LogLock.acquire()
		print(f"getPosition_API : {vehicle_name}, ({x}, {y}, {z})")
		LogLock.release()
		return (x, y)
	
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
		return dest 

	# Behaviors
	def cover_Behavior(self, *rpc_args, vehicle_name):
		LogLock.acquire()
		print("cover_Behavior : ", vehicle_name)
		LogLock.release()

	def takeOff_Behavior(self, *rpc_args, vehicle_name):
		LogLock.acquire()
		print("takeOff_Behavior : ", vehicle_name)
		LogLock.release()

	def flyCircle_Behavior(self, *rpc_args, vehicle_name):
		LogLock.acquire()
		print("flyCircle_Behavior : ", vehicle_name)
		LogLock.release()

	# Tasks
	def search(self, vehicle_name_list):
		LogLock.acquire()
		print("search : ", vehicle_name_list)
		LogLock.release()