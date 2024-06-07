import threading
import airsim
import math

LogLock = threading.Lock()
Lock = threading.Lock()

def takeOff_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	res = client.takeoffAsync(vehicle_name=vehicle_name)
	# Lock.acquire()
	res.join()
	# Lock.release()


def flyToHeight_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]

	pose = client.simGetVehiclePose(vehicle_name=vehicle_name)
	res = client.moveToPositionAsync(pose.position.x_val, pose.position.y_val, -swarm_args[0], 10, vehicle_name=vehicle_name)

	# Lock.acquire()
	res.join()
	# Lock.release()


def getPosition_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]
	pos = client.simGetVehiclePose(vehicle_name=vehicle_name)
	home = kwargs["wrapper"].home

	pos.position.x_val += home[vehicle_name].position.x_val
	pos.position.y_val += home[vehicle_name].position.y_val
	pos.position.z_val += home[vehicle_name].position.z_val 
	return (pos.position.x_val, pos.position.y_val, pos.position.z_val)


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
	mapper = {
		"search_uav_0": 0,
		"search_uav_1": 1,
		"search_uav_2": 2
	}
	index = mapper[vehicle_name]
	traces = swarm_args[0][index]
	pos = swarm_args[1]
	
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
	return (dest[0], dest[1], pos[2]) 


def flyTo_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]
	destination = swarm_args[0]	# World coordinate system
	home = kwargs["wrapper"].home

	# Relative coordinate system
	relative_destination_x = destination[0] - home[vehicle_name].position.x_val
	relative_destination_y = destination[1] - home[vehicle_name].position.y_val
	relative_destination_z = destination[2] - home[vehicle_name].position.z_val

	res = client.moveToPositionAsync(relative_destination_x, relative_destination_y, relative_destination_z, 2, vehicle_name=vehicle_name)
	# Lock.acquire()
	res.join()
	# Lock.release()


# def flyCircle_v0_API(*swarm_args, **kwargs):
# 	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
# 	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]
# 	state = swarm_args[0]
# 	radius = swarm_args[1]

# 	import math
# 	start_position = behavior["flyCircle"]["start_position_on_circle"][vehicle_name]
# 	circle_center = (round(start_position.position.x_val), round(start_position.position.y_val) + radius)
# 	vx = state.kinematics_estimated.linear_velocity.x_val / radius
# 	vy = state.kinematics_estimated.linear_velocity.y_val / radius
# 	theta = math.atan2(vy, vx)
	
# 	import numpy as np
# 	flyCircle_state = np.array([(start_position.position.x_val - circle_center[0]) / radius, 
# 								(start_position.position.y_val - circle_center[1]) / radius, 0], dtype=np.float32)
# 	agent = behavior["flyCircle"]["agent"]
# 	action = agent.choose_action(flyCircle_state)
# 	new_vx = math.cos(theta + action[0]) * radius / 2
# 	new_vy = math.sin(theta + action[0]) * radius / 2
# 	hover_z = state.kinematics_estimated.position.z_val
# 	client.moveByVelocityZAsync(vx=new_vx, vy=new_vy, z=hover_z, duration=1, vehicle_name=vehicle_name)


# def flyCircle_API(*swarm_args, **kwargs):
# 	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
# 	client:airsim.MultirotorClient = kwargs["wrapper"].clients[vehicle_name]
# 	TD3agent = swarm_args[0]
# 	radius = swarm_args[1]
	
# 	start_position = behavior["flyCircle"]["start_position_on_circle"][vehicle_name]
# 	circle_center = (round(start_position.position.x_val), round(start_position.position.y_val) + radius)
# 	LogLock.acquire()
# 	print(f"vehicle_name = {vehicle_name}, start = {start_position}, center = {circle_center}")
# 	LogLock.release()

# 	import math
# 	import numpy as np
# 	step_count = 0
# 	while True:
# 		state = getState_API(vehicle_name=vehicle_name)
# 		vx = state.kinematics_estimated.linear_velocity.x_val
# 		vy = state.kinematics_estimated.linear_velocity.y_val
# 		theta = math.atan2(vy, vx)
# 		flyCircle_state = np.array([(state.kinematics_estimated.position.x_val - circle_center[0]) / radius, 
# 									(state.kinematics_estimated.position.y_val - circle_center[1]) / radius, theta], dtype=np.float32)

# 		action = TD3agent.choose_action(flyCircle_state)
# 		LogLock.acquire()
# 		print(f"state = {flyCircle_state}, action = {action}")
# 		LogLock.release()
# 		new_vx = math.cos(theta + action[0]) * radius / 2
# 		new_vy = math.sin(theta + action[0]) * radius / 2
# 		new_v = math.sqrt(new_vx**2 + new_vy**2)
# 		hover_z = state.kinematics_estimated.position.z_val
# 		# new_x = state.kinematics_estimated.position.x_val + new_vx * 0.1
# 		# new_y = state.kinematics_estimated.position.y_val + new_vy * 0.1
# 		# client.moveToPositionAsync(x=new_x, y=new_y, z=hover_z, velocity=new_v, vehicle_name=vehicle_name)
# 		client.moveByVelocityZAsync(vx=new_vx, vy=new_vy, z=hover_z, duration=1, vehicle_name=vehicle_name)

# 		distance_to_start_position = math.sqrt((state.kinematics_estimated.position.x_val - start_position.position.x_val)**2 + (state.kinematics_estimated.position.y_val - start_position.position.y_val)**2)

# 		if (distance_to_start_position < 0.1 *radius and step_count >= 1000) or step_count > 50000:
# 			break

# 		step_count += 1

