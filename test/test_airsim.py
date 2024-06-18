import pprint
import re
import airsim
import threading
import time

LOCK = threading.Lock()

client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)


def set_global_camera():
	global_camera = "GlobalCamera"
	client.enableApiControl(True, global_camera)
	client.takeoffAsync(vehicle_name=global_camera).join()
	client.moveToPositionAsync(0, 0, -40, 10, vehicle_name=global_camera).join()

	airsim.wait_key()


def agent_work(agent_id):
	pose = airsim.Pose(
		airsim.Vector3r(0, agent_id * 2, 0), airsim.to_quaternion(0, 0, 0)
	)
	h = agent_id * 10
	LOCK.acquire()
	client.simAddVehicle(f"uav_{agent_id}", "simpleflight", pose)
	LOCK.release()
	LOCK.acquire()
	client.enableApiControl(True, f"uav_{agent_id}")
	LOCK.release()
	time.sleep(2)
	LOCK.acquire()
	client.simGetVehiclePose(vehicle_name=f"uav_{agent_id}")
	LOCK.release()
	res = client.moveToPositionAsync(
		0, agent_id * 2, -h, 10, vehicle_name=f"uav_{agent_id}"
	)
	LOCK.acquire()
	res.join()
	LOCK.release()


def multitask():
	threads = []
	for now in range(1, 4):
		thread = threading.Thread(target=agent_work, args=(now,))
		threads.append(thread)

	# start all threads
	for thread in threads:
		thread.start()

	# wait for all threads finish
	for thread in threads:
		thread.join()


def list_cars():
	# assets = client.simListAssets()
	# pprint.pprint(f"assets = {assets}")
	senceObj = client.simListSceneObjects()
	car_pattern = re.compile(r'^Car_\d+$')
	cars = [obj for obj in senceObj if car_pattern.match(obj) ]
	cars_positions = {
		car_name: (round(pose.x_val), round(pose.y_val))
		for car_name in cars
		if (pose := client.simGetObjectPose(object_name=car_name).position)
	}
	pprint.pprint(cars_positions)
	# vehicles = client.listVehicles()
	# pprint.pprint(f"vehicles = {vehicles}")

if __name__ == "__main__":
	set_global_camera()
	vehicle_name = "GlobalCamera"
	response = client.simGetImage("bottom_center", airsim.ImageType.Scene, vehicle_name=vehicle_name)

	import os
	current_file_path = os.path.abspath(__file__)
	current_directory = os.path.dirname(current_file_path)
	import datetime
	time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	vehicle_directory = os.path.join(current_directory, "data", vehicle_name)
	filename = os.path.join(vehicle_directory, f"{time_str}.png")
	if not os.path.exists(vehicle_directory):
		os.makedirs(vehicle_directory)
	with open(filename, "wb") as f:
		f.write(response)

