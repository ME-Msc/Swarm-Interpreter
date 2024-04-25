import airsim
import time


client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)

def init_camera():
	global_camera = "GlobalCamera"
	client.enableApiControl(True, global_camera)
	client.takeoffAsync(vehicle_name=global_camera).join()
	client.moveToPositionAsync(0, 0, -40, 10, vehicle_name=global_camera).join()

	airsim.wait_key()

def create_agent():
	agent_list = []
	for agent_id in range(1, 4):
		pose = airsim.Pose(airsim.Vector3r(0, agent_id * 2, 0), airsim.to_quaternion(0, 0, 0))
		client.simAddVehicle(f'uav_{agent_id}', "simpleflight", pose)
		client.enableApiControl(True, f'uav_{agent_id}')
		agent_list.append(agent_id)
	time.sleep(2)
	return agent_list

def agent_work(agent_id, each_order = True):
	cnt = 0
	while cnt < 3:
		h = agent_id * 5
		res = client.moveToPositionAsync(0, agent_id * 2, -h, 10, vehicle_name=f'uav_{agent_id}')
		if not each_order:
			res.join()
		cnt += 1
		yield

def main():
	init_camera()
	agent_list = create_agent()
	work_generators = [agent_work(agt, False) for agt in agent_list]
	for _ in range(3):  # 假设你希望每个agent执行3次工作
		for gen in work_generators:
			try:
				next(gen)
			except StopIteration:
				pass  # 如果生成器已经没有值可以生成，就会引发StopIteration异常
		
if __name__ == "__main__":
	main()
