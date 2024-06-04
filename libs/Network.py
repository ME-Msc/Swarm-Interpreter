import os

from libs.RL.td3 import TD3Agent

agent = TD3Agent(3, 1)
current_file_path = os.path.abspath(__file__)
current_directory = os.path.dirname(current_file_path)
agent.load(current_directory+"/RL/fly_circle.pkl")

TD3_fly_circle = agent