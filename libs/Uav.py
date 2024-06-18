import threading
import airsim

LogLock = threading.Lock()

def takeOff_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	res = client.takeoffAsync(vehicle_name=vehicle_name)
	res.join()


def flyToHeight_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	# pose = client.simGetVehiclePose(vehicle_name=vehicle_name)
	res = client.moveToZAsync(-swarm_args[0], 10, vehicle_name=vehicle_name)
	# res = client.moveToPositionAsync(pose.position.x_val, pose.position.y_val, -swarm_args[0], 10, vehicle_name=vehicle_name)
	res.join()


def getPosition_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]
	pos = client.simGetVehiclePose(vehicle_name=vehicle_name)
	home = kwargs["wrapper"].home

	pos.position.x_val += home[vehicle_name].position.x_val
	pos.position.y_val += home[vehicle_name].position.y_val
	pos.position.z_val += home[vehicle_name].position.z_val 
	return pos


def getState_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]
	state:airsim.MultirotorState = client.getMultirotorState(vehicle_name=vehicle_name)
	home = kwargs["wrapper"].home

	state.kinematics_estimated.position.x_val += home[vehicle_name].position.x_val
	state.kinematics_estimated.position.y_val += home[vehicle_name].position.y_val
	state.kinematics_estimated.position.z_val += home[vehicle_name].position.z_val 
	return state


def getDestination_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	mapper = {
		"search_uav_0": 0,
		"search_uav_1": 1,
		"search_uav_2": 2
	}
	index = mapper[vehicle_name]
	traces = swarm_args[0][index]
	pos = (swarm_args[1].position.x_val, swarm_args[1].position.y_val, swarm_args[1].position.z_val)
	
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
	res = airsim.Pose(airsim.Vector3r(dest[0], dest[1], pos[2]))
	return res


def flyTo_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]
	destination = swarm_args[0]	# World coordinate system
	home = kwargs["wrapper"].home

	# Relative coordinate system
	relative_destination_x = destination.position.x_val - home[vehicle_name].position.x_val
	relative_destination_y = destination.position.y_val - home[vehicle_name].position.y_val
	relative_destination_z = destination.position.z_val - home[vehicle_name].position.z_val

	res = client.moveToPositionAsync(relative_destination_x, relative_destination_y, relative_destination_z, 2, vehicle_name=vehicle_name)
	res.join()


def flyCircle_API(*swarm_args, **kwargs):
	TD3agent = swarm_args[0]
	radius = swarm_args[1]
	start_position = swarm_args[2]

	circle_center = (round(start_position.position.x_val), round(start_position.position.y_val) + radius)

	# LogLock.acquire()
	# vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	# print(f"vehicle_name = {vehicle_name}, start = {start_position}, center = {circle_center}")
	# LogLock.release()

	TD3agent.one_round(getState_func = getState_API, circle_agent = TD3agent, radius = radius, start_position = start_position, circle_center = circle_center, **kwargs)


def takePicture_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]
	
	response = client.simGetImage("bottom_center", airsim.ImageType.Scene, vehicle_name=vehicle_name)

	# import os
	# current_file_path = os.path.abspath(__file__)
	# current_directory = os.path.dirname(current_file_path)
	# import datetime
	# time_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
	# vehicle_directory = os.path.join(current_directory, "data", vehicle_name)
	# filename = os.path.join(vehicle_directory, f"{time_str}.png")
	# if not os.path.exists(vehicle_directory):
	# 	os.makedirs(vehicle_directory)
	# with open(filename, "wb") as f:
	# 	f.write(response)

	return response