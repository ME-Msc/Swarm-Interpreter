import threading
import time
import copy
import airsim
from interpreter.rpc.searchTspSolver import searchTspSolver

LogLock = threading.Lock()


class AirsimWrapper:
	def __init__(self, wait_or_not=True):
		# connect to the AirSim simulator
		self.clients = {}
		self.home = {}
		self.lock = threading.Lock()
		self.task = {}

		if wait_or_not:
			# set_global_camera
			client = airsim.MultirotorClient()
			self.clients["GlobalCamera"] = client
			self.clients["GlobalCamera"].confirmConnection()
			self.clients["GlobalCamera"].enableApiControl(True)
			self.clients["GlobalCamera"].takeoffAsync().join()
			self.clients["GlobalCamera"].moveToPositionAsync(0, 0, -80, 10).join()
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
			client.simSetTraceLine(color_rgba=[1.0, 0, 0, 0], thickness=30.0, vehicle_name=vhcl_nm)
		time.sleep(2)


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


	def getPositon_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		pos = client.simGetVehiclePose(vehicle_name=vehicle_name)
		pos.position.x_val += self.home[vehicle_name].position.x_val
		pos.position.y_val += self.home[vehicle_name].position.y_val
		pos.position.z_val += self.home[vehicle_name].position.z_val 
		return pos

	
	def getNextDestination_API(self, *rpc_args, vehicle_name):
		now_location = rpc_args[0]
		task = self.task["search"]
		vehicle_id = task.id[vehicle_name]
		search_task_next_step = task.get_i_vehicle_next_step_location(vehicle_id, now_location.position.x_val, now_location.position.y_val)
		next_destination = copy.deepcopy(now_location)
		next_destination.position.x_val = search_task_next_step[0]
		next_destination.position.y_val = search_task_next_step[1]
		next_destination.position.z_val = round(next_destination.position.z_val)
		
		LogLock.acquire()
		print(f'##### {vehicle_name} \n##### now_location=({now_location.position.x_val}, {now_location.position.y_val}, {now_location.position.z_val}) \n##### next_destination=({next_destination.position.x_val}, {next_destination.position.y_val}, {next_destination.position.z_val})\n')
		LogLock.release()
		
		return next_destination
		

	def flyTo_API(self, *rpc_args, vehicle_name):
		client:airsim.MultirotorClient = self.clients[vehicle_name]
		target = rpc_args[0].position
		
		LogLock.acquire()
		print(f'!!!!! {vehicle_name}, id={id(vehicle_name)}\n!!!!! target = {target}\n')
		LogLock.release()

		absolute_target_x = target.x_val - self.home[vehicle_name].position.x_val
		absolute_target_y = target.y_val - self.home[vehicle_name].position.y_val
		absolute_target_z = target.z_val - self.home[vehicle_name].position.z_val

		res = client.moveToPositionAsync(absolute_target_x, absolute_target_y,absolute_target_z, 2, vehicle_name=vehicle_name)
		self.lock.acquire()
		res.join()
		self.lock.release()


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

