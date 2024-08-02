import inspect
import threading
import time

LogLock = threading.Lock()
MIN_THRESHOLD = 2

def takeOff_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	LogLock.acquire()
	print(f"{vehicle_name} :-> {inspect.currentframe().f_code.co_name}")
	LogLock.release()


def flyToHeight_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	LogLock.acquire()
	print(f"{vehicle_name} :-> {inspect.currentframe().f_code.co_name}")
	LogLock.release()


def getPosition_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	return (0, 0, 0)


def getState_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	return 0


def getDestination_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'

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
	
	return (dest[0], dest[1], pos[2])


def flyTo_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	destination = swarm_args[0]	# World coordinate system
	LogLock.acquire()
	print(f"{vehicle_name} :-> {inspect.currentframe().f_code.co_name}, ({destination})")
	LogLock.release()
	time.sleep(3)


def flyCircle_API(*swarm_args, **kwargs):
	TD3agent = swarm_args[0]
	radius = swarm_args[1]
	start_position = swarm_args[2]

	circle_center = (round(start_position.position.x_val), round(start_position.position.y_val) + radius)

	TD3agent.one_round(getState_func = getState_API, circle_agent = TD3agent, radius = radius, start_position = start_position, circle_center = circle_center, **kwargs)


def takePicture_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	LogLock.acquire()
	print(f"{vehicle_name} :-> {inspect.currentframe().f_code.co_name}")
	LogLock.release()
	return "fake picture"

def pickUp_API(*swarm_args, **kwargs):
	vehicle_name = f'{kwargs["agent"]}_{kwargs["id"]}'
	LogLock.acquire()
	print(f"{vehicle_name} :-> {inspect.currentframe().f_code.co_name}")
	LogLock.release()
