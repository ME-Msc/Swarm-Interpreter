from __future__ import print_function

import logging

import grpc
import swarm_pb2
import swarm_pb2_grpc

def createUavs(cnt):
    print("Creating %d Uavs." % cnt)
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = swarm_pb2_grpc.SwarmStub(channel)
        print(swarm_pb2.CreateUavsRequest(uav_cnt = cnt))
        response = stub.createUavs(swarm_pb2.CreateUavsRequest(uav_cnt = cnt))
    print("Swarm client received: " + response.message)

def resetWorld():
    print("Reset world.")
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = swarm_pb2_grpc.SwarmStub(channel)
        print(swarm_pb2.ResetWorldRequest())
        response = stub.resetWorld(swarm_pb2.ResetWorldRequest())
    print("Swarm client received: " + response.message)

def treesGo(id):
    # NOTE(gRPC Python Team): .close() is possible on a channel and should be
    # used in circumstances in which the with statement does not fit the needs
    # of the code.
    print("Will try to move ...")
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = swarm_pb2_grpc.SwarmStub(channel)
        print(swarm_pb2.TreesGoRequest(uav_id = 0))
        response = stub.trees_go_RPC_call(swarm_pb2.TreesGoRequest(uav_id = id))
    print("Swarm client received: " + response.message)



if __name__ == "__main__":
    logging.basicConfig()
    uav_count = 3
    createUavs(uav_count)
    resetWorld()
    for i in range(uav_count):
        treesGo(i)
