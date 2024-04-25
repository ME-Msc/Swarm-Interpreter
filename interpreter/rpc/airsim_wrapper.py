from queue import Queue
import threading
import time

import airsim


class AirsimWrapper:
	def __init__(self, rpc_queue:Queue):
		# connect to the AirSim simulator
		self.client = airsim.MultirotorClient()
		self.client.confirmConnection()
		self.client.enableApiControl(True)
		self.home = {}
		self.rpc_queue = rpc_queue

		def set_global_camera():
			global_camera = "GlobalCamera"
			self.client.enableApiControl(True, global_camera)
			self.client.takeoffAsync(vehicle_name=global_camera).join()
			self.client.moveToPositionAsync(0, 0, -20, 10, vehicle_name=global_camera).join()
			self.client.hoverAsync(global_camera).join()

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
			pose = airsim.Pose(airsim.Vector3r(group, i * 2, 0), airsim.to_quaternion(0, 0, 0))
			self.client.simAddVehicle(agents_list[i], "simpleflight", pose)
			self.home[agents_list[i]] = pose
			self.client.enableApiControl(True, agents_list[i])
		# self.client.armDisarm(True, agents_list[i])
		time.sleep(2)

	def takeOff_API(self, *rpc_args, vehicle_name, each_order=False):
		def rpc_call():
			res = self.client.takeoffAsync(vehicle_name=vehicle_name)
			if not each_order:
				res.join()
		self.rpc_queue.put((rpc_call, vehicle_name))  # 将RPC调用和车辆名称一起放入队列

	def flyToHeight_API(self, *rpc_args, vehicle_name, each_order=False):
		h = round(rpc_args[0])
		def rpc_call(h=h):
			pose = self.client.simGetVehiclePose(vehicle_name=vehicle_name)
			tar_x, tar_y = round(pose.position.x_val), round(pose.position.y_val)
			res = self.client.moveToPositionAsync(tar_x, tar_y, -h, 10, vehicle_name=vehicle_name)
			if not each_order:
				res.join()
		self.rpc_queue.put((rpc_call, vehicle_name))  # 将RPC调用和车辆名称一起放入队列


if __name__ == '__main__':
	rpc_queue = Queue()
	semaphore_dict = {}
	
	def rpc_consumer(q:Queue, sem_dic:dict):
		while True:
			rpc_call, vehicle_name = q.get()
			try:
				rpc_call()
			except Exception as e:
				print(e)
			finally:
				sem_dic[vehicle_name].release()
			q.task_done()

	def swarm_producer(q:Queue, sem_dic:dict, each_order=False):
		wrapper = AirsimWrapper(rpc_queue=q)
		uav_list = [f'uav_{i}' for i in range(1, 5)]
		wrapper.set_home(uav_list)
		def agent_work(i):
			veh_nm = f'uav_{i}'
			sem_dic[veh_nm] = threading.Semaphore(1)
			sem_dic[veh_nm].acquire()
			wrapper.takeOff_API(vehicle_name=veh_nm, each_order=each_order)

			sem_dic[veh_nm].acquire()
			wrapper.flyToHeight_API(i*10, vehicle_name=veh_nm, each_order=each_order)

		agent_threads = []
		for i in range(1, 5):
			thread = threading.Thread(target=agent_work, args=(i, ))
			agent_threads.append(thread)

		# start all threads
		for thread in agent_threads:
			thread.start()

		# wait for all threads finish
		for thread in agent_threads:
			thread.join()
	
	rpc_thread = threading.Thread(target=rpc_consumer, args=(rpc_queue, semaphore_dict))
	rpc_thread.start()
	
	main_thread = threading.Thread(target=swarm_producer, args=(rpc_queue, semaphore_dict, True)) # True:test each
	main_thread.start()

	rpc_thread.join()
	main_thread.join()