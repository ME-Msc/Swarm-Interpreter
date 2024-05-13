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
		# connect to the AirSim simulator
		self.clients = {}
		self.home = {}
		self.lock = threading.Lock()
		self.task = {}
		self.behavior = {}

	def copy(self):
		new_wrapper = TestWrapper(wait_or_not=False)
		for k, v in self.clients.items():
			if k != "GlobalCamera":
				new_wrapper.clients[k] = self.clients[k]
		new_wrapper.home = copy.deepcopy(self.home)
		new_wrapper.lock = threading.Lock()
		new_wrapper.task = copy.deepcopy(self.task)
		return new_wrapper

	def set_home(self, agents_list: list):
		print("set_home : ", agents_list)

	# RPC
	def takeOff_API(self, *rpc_args, vehicle_name):
		print("takeOff_API : ", vehicle_name)

	def flyToHeight_API(self, *rpc_args, vehicle_name):
		print("flyToHeight_API : ", vehicle_name)
		
	def getState_API(self, *rpc_args, vehicle_name):
		print("getState_API : ", vehicle_name)

	def getTspDestination_API(self, *rpc_args, vehicle_name):
		print("getTspDestination_API : ", vehicle_name)
		
	def flyTo_API(self, *rpc_args, vehicle_name):
		print("flyTo_API : ", vehicle_name)

	def flyCircle_API(self, *rpc_args, vehicle_name):
		print("flyCircle_API : ", vehicle_name)
		
	# Behaviors
	def search_Behavior(self, *rpc_args, vehicle_name):
		print("search_Behavior : ", vehicle_name)

	def takeOff_Behavior(self, *rpc_args, vehicle_name):
		print("takeOff_Behavior : ", vehicle_name)

	def flyCircle_Behavior(self, *rpc_args, vehicle_name):
		print("flyCircle_Behavior : ", vehicle_name)

	# Tasks
	def search(self, vehicle_name_list):
		print("search : ", vehicle_name_list)
