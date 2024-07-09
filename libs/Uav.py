import threading
import time
import airsim
import inspect

LogLock = threading.Lock()
MIN_THRESHOLD = 2

def takeOff_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	Lock = kwargs["wrapper"].locks[vehicle_name]
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	Lock.acquire()
	res = client.takeoffAsync(vehicle_name=vehicle_name)
	res.join()
	Lock.release()
	'''
	th = threading.Thread(target=lambda: res.join())
	th.start()
	while True:
		if not th.is_alive():
			break
		# dosomething
		time.sleep(0.01)
	th.join()
	'''
	'''
	if hasattr(kwargs["wrapper"], "clients"):
	else:
		LogLock.acquire()
		print(f"{vehicle_name} :-> {inspect.currentframe().f_code.co_name}")
		LogLock.release()
	'''


def flyToHeight_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	Lock = kwargs["wrapper"].locks[vehicle_name]
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	while True:
		Lock.acquire()
		pos = client.simGetVehiclePose(vehicle_name=vehicle_name)
		Lock.release()
		time.sleep(0.5)
		if abs(pos.position.z_val - (-swarm_args[0])) < MIN_THRESHOLD:
			break
		Lock.acquire()
		res = client.moveToPositionAsync(pos.position.x_val, pos.position.y_val, -swarm_args[0], 5, vehicle_name=vehicle_name)
		Lock.release()
		time.sleep(0.5)


def getPosition_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	Lock = kwargs["wrapper"].locks[vehicle_name]
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]
	Lock.acquire()
	pos = client.simGetVehiclePose(vehicle_name=vehicle_name)
	Lock.release()
	time.sleep(0.5)
	home = kwargs["wrapper"].home

	pos.position.x_val += home[vehicle_name].position.x_val
	pos.position.y_val += home[vehicle_name].position.y_val
	pos.position.z_val += home[vehicle_name].position.z_val 
	# return pos
	return (pos.position.x_val, pos.position.y_val, pos.position.z_val)


def getState_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	Lock = kwargs["wrapper"].locks[vehicle_name]
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	Lock.acquire()
	state:airsim.MultirotorState = client.getMultirotorState(vehicle_name=vehicle_name)
	Lock.release()
	time.sleep(0.5)
	home = kwargs["wrapper"].home

	state.kinematics_estimated.position.x_val += home[vehicle_name].position.x_val
	state.kinematics_estimated.position.y_val += home[vehicle_name].position.y_val
	state.kinematics_estimated.position.z_val += home[vehicle_name].position.z_val 
	return state


def getDestination_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	Lock = kwargs["wrapper"].locks[vehicle_name]
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	mapper = {
		"search_drone_0": 0,
		"search_drone_1": 1,
		"search_drone_2": 2
	}
	index = mapper[vehicle_name]
	traces = swarm_args[0][index]
	# pos = (swarm_args[1].position.x_val, swarm_args[1].position.y_val, swarm_args[1].position.z_val)
	pos = swarm_args[1]
	
	min_distance = float('inf')
	closest_index = -1
	dest = traces[closest_index]
	
	import math
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
	
	# res = airsim.Pose(airsim.Vector3r(dest[0], dest[1], pos[2]))
	# return res
	return (dest[0], dest[1], pos[2])


def flyTo_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	Lock = kwargs["wrapper"].locks[vehicle_name]
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	destination = swarm_args[0]	# World coordinate system
	home = kwargs["wrapper"].home

	# Relative coordinate system
	relative_destination_x = destination[0] - home[vehicle_name].position.x_val
	relative_destination_y = destination[1] - home[vehicle_name].position.y_val
	relative_destination_z = destination[2] - home[vehicle_name].position.z_val

	# import datetime
	# time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	LogLock.acquire()
	print(f"{vehicle_name} fly to {relative_destination_x}, {relative_destination_y}, {relative_destination_z}")
	LogLock.release()
	while True:
		pos = getPosition_API(**kwargs)
		import math
		if math.dist((pos[0], pos[1], pos[2]), (destination[0], destination[1], destination[2])) < MIN_THRESHOLD:
			break
		Lock.acquire()
		res = client.moveToPositionAsync(relative_destination_x, relative_destination_y, relative_destination_z, 2, vehicle_name=vehicle_name)
		Lock.release()
		time.sleep(0.5)


def flyCircle_API(*swarm_args, **kwargs):
	TD3agent = swarm_args[0]
	radius = swarm_args[1]
	start_position = swarm_args[2]

	circle_center = (round(start_position[0]), round(start_position[1]) + radius)

	TD3agent.one_round(getState_func = getState_API, circle_agent = TD3agent, radius = radius, start_position = start_position, circle_center = circle_center, **kwargs)


def takePicture_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	Lock = kwargs["wrapper"].locks[vehicle_name]
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	import datetime
	# print(str(datetime.datetime.now()) + " Enter takePicture_API")
	time.sleep(5)
	Lock.acquire()
	response = client.simGetImage("bottom_center", airsim.ImageType.Scene, vehicle_name=vehicle_name)
	Lock.release()

	import os
	current_file_path = os.path.abspath(__file__)
	current_directory = os.path.dirname(current_file_path)
	time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	vehicle_directory = os.path.join(current_directory, "data", vehicle_name)
	filename = os.path.join(vehicle_directory, f"{time_str}.png")
	if not os.path.exists(vehicle_directory):
		os.makedirs(vehicle_directory)
	with open(filename, "wb") as f:
		f.write(response)

	return filename


def pickUp_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	LogLock.acquire()
	print(f"{vehicle_name} :-> {inspect.currentframe().f_code.co_name}")
	LogLock.release()


def dropGoods_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	LogLock.acquire()
	print(f"{vehicle_name} :-> {inspect.currentframe().f_code.co_name}")
	LogLock.release()


def goHome_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	Lock = kwargs["wrapper"].locks[vehicle_name]
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	client.goHomeAsync(vehicle_name=vehicle_name)
	LogLock.acquire()
	print(f"{vehicle_name} :-> {inspect.currentframe().f_code.co_name}")
	LogLock.release()


def print_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	LogLock.acquire()
	print(f"{vehicle_name} : {swarm_args[:-1]})")
	LogLock.release()