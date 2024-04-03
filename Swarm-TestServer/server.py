import grpc
from concurrent import futures
import threading
import numpy as np

import pygame
import queue

import swarm_pb2
import swarm_pb2_grpc
from uav.sim_uav import SimUav
from env.trees_go_world import TreesGoWorld

class Server(swarm_pb2_grpc.SwarmServicer):
    def __init__(self, que):
        super().__init__()
        self.uavs = []
        self.world = TreesGoWorld(que=que)
        self.queue = que

    def createUavs(self, request, context):
        print("Server recieved createUavs( %d )" % request.uav_cnt)
        home_choices = [[1.6, 1.2], [0.1, 1.2], [-1.1, 1.2], [-2.3, 1.2]]
        self.uavs.extend([SimUav(i, home_choices[i%4]) for i in range(len(self.uavs), len(self.uavs)+request.uav_cnt)])
        return swarm_pb2.CommonReply(message="Create %d Uavs successfully." % request.uav_cnt)

    def resetWorld(self, request, context):
        print("Server recieved resetWorld().")
        self.world = TreesGoWorld(que=self.queue)
        for uav in self.uavs:
            uav.set_world(self.world)
            self.world.set_uavs([], self.uavs)
        return swarm_pb2.CommonReply(message="Reset world successfully.")

    def trees_go_RPC_call(self, request, context):
        print("Server recieved trees_go_RPC_call from %d" % request.uav_id)
        for uav in self.world.uavs:
            if uav.id == request.uav_id:
                uav.trees_go_RPC_call()
                break
        return swarm_pb2.CommonReply(message="Reply to %d's trees_go_RPC_call!" % request.uav_id)


class Render():
    def __init__(self, que) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((600, 600))
        self.offset = np.array([300, 500])
        self.scale = 75
        self.queue = que
        self.data = None

    def render(self):
        self.screen.fill("white")
        if not self.queue.empty():
            self.data = self.queue.get()
        if self.data is not None:
            for obstacle in self.data['obstacles']:
                pos = obstacle[:2]
                pygame.draw.circle(self.screen, "green", pos * self.scale + self.offset, 5)

            for uav in self.data['uavs']:
                pos, theta = uav[0], uav[1]
                color = "blue"
                pygame.draw.circle(self.screen, color, pos * self.scale + self.offset, 5)

                line_len = 20
                st = pos * self.scale + self.offset
                ed = st[0] + np.cos(theta).item() * line_len, st[1] + np.sin(theta).item() * line_len
                pygame.draw.line(self.screen, "black", st, ed)

            for tar in self.data['targets']:
                pygame.draw.circle(self.screen, "red", np.array(tar) * self.scale + self.offset, 5)

        pygame.display.flip()


def server_run(q):
    port = "50051"
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    swarm_pb2_grpc.add_SwarmServicer_to_server(Server(q), server)
    server.add_insecure_port("[::]:" + port)
    server.start()
    print("Server started, listening on " + port)
    server.wait_for_termination()

def render_run(q):
    r = Render(q)
    clock = pygame.time.Clock()
    running = True
    while running:
        pygame.event.pump()  # 处理所有事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        r.render()
        pygame.display.flip()
        clock.tick(60)  # 控制帧率

    pygame.quit()

if __name__ == '__main__':
    msg_q = queue.Queue()
    server_thread = threading.Thread(target=server_run, args=(msg_q, ))
    
    server_thread.start()
    
    render_run(msg_q)