import math
import time
import airsim
import numpy as np
import os

from interpreter.rpc.RL.td3 import TD3Agent

def uav_flyCircle(clt:airsim.MultirotorClient, vhcl_nm, radius=1):
    agent = TD3Agent(3, 1)
    current_file_path = os.path.abspath(__file__)
    current_directory = os.path.dirname(current_file_path)
    agent.load(current_directory+"/RL/fly_circle.pkl")

    clt.simSetTraceLine(color_rgba=[1.0, 0, 0, 0], thickness=10.0, vehicle_name=vhcl_nm)
    airsim.wait_key()
    clt.takeoffAsync(vehicle_name=vhcl_nm)
    clt.moveToPositionAsync(x=0, y=0, z=-30, velocity=10, vehicle_name=vhcl_nm).join()
    
    start_pos = clt.simGetVehiclePose(vehicle_name=vhcl_nm)
    circle_center = (round(start_pos.position.x_val), round(start_pos.position.y_val)+radius)
    state = np.array([(start_pos.position.x_val-circle_center[0])/radius, (start_pos.position.y_val-circle_center[1])/radius, 0], dtype=np.float32)
    done = False
    
    clt.moveByVelocityAsync(vx=1*radius, vy=0, vz=0, duration=1, vehicle_name=vhcl_nm)
    while not done:
        time.sleep(0.2)
        action = agent.choose_action(state)
        # print(f'state = {state} , action = {action}')

        airsim_state = clt.getMultirotorState(vehicle_name=vhcl_nm)
        vx = airsim_state.kinematics_estimated.linear_velocity.x_val / radius
        vy = airsim_state.kinematics_estimated.linear_velocity.y_val / radius
        theta = math.atan2(vy, vx)
        # print(f'vx = {vx}, vy = {vy} , {theta}')
        new_vx = math.cos(theta + action[0])*radius/2
        new_vy = math.sin(theta + action[0])*radius/2
        hover_z = airsim_state.kinematics_estimated.position.z_val
        clt.moveByVelocityZAsync(vx=new_vx, vy=new_vy, z=hover_z, duration=1, vehicle_name=vhcl_nm)

        pos = clt.simGetVehiclePose(vehicle_name=vhcl_nm)
        state = np.array([pos.position.x_val-circle_center[0], pos.position.y_val-circle_center[1], theta+action[0]], dtype=np.float32)


if __name__ == "__main__":
    client = airsim.MultirotorClient()
    client.confirmConnection()
    client.enableApiControl(True)
    uav_flyCircle(clt=client, vhcl_nm="GlobalCamera", radius=10)