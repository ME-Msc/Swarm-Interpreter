import math
import threading
import time
import copy
import airsim

LogLock = threading.Lock()


class Wrapper:
	def __init__(self) -> None:
		self.home = {}

	def copy(self):
		new_wrapper = self.__class__()
		new_wrapper.home = copy.deepcopy(self.home)
		return new_wrapper
	
	def set_home(self, agents_list:list):
		group = len(self.home)
		for i in range(len(agents_list)):
			vhcl_nm = agents_list[i]
			pose = (group, i*2, 0)
			self.home[vhcl_nm] = pose
		time.sleep(2)


class AirsimWrapper(Wrapper):
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