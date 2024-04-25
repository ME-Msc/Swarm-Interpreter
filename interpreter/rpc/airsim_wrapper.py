import threading
import time

import airsim


class AirsimWrapper:
	def __init__(self):
		# connect to the AirSim simulator
		self.clients = {}
		self.home = {}
		self.lock = threading.Lock()

		def set_global_camera():
			client = airsim.MultirotorClient()
			global_camera = "GlobalCamera"
			self.clients[global_camera] = client
			self.clients[global_camera].confirmConnection()
			self.clients[global_camera].enableApiControl(True)
			self.clients[global_camera].takeoffAsync().join()
			self.clients[global_camera].moveToPositionAsync(0, 0, -20, 10).join()
			self.clients[global_camera].hoverAsync().join()

		set_global_camera()
		message = (
			"1. Push / to switch to chase with spring arm mode.\n"
			"2. Wait for the drone to fly to an altitude of 300 meters.\n"
			"3. Push M to switch to manual camera control.\n"
			"4. Push S to move the view downwards, regard the drone as a global camera.\n"
			"5. Press any key to continue after the global camera is ready."
		)
		airsim.wait_key(message=message)

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
		time.sleep(2)

	def takeOff_API(self, *rpc_args, vehicle_name):
		client = self.clients[vehicle_name]

		res = client.takeoffAsync(vehicle_name=vehicle_name)
		self.lock.acquire()
		res.join()
		self.lock.release()

	def flyToHeight_API(self, *rpc_args, vehicle_name):
		client = self.clients[vehicle_name]
		
		h = rpc_args[0]
		pose = client.simGetVehiclePose(vehicle_name=vehicle_name)
		res = client.moveToPositionAsync(pose.position.x_val, pose.position.y_val, -h, 10, vehicle_name=vehicle_name)
		self.lock.acquire()
		res.join()
		self.lock.release()

