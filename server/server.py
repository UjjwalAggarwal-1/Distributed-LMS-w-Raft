import os
import sys
from concurrent import futures

import grpc
from grpc_server import LMSService

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "proto"))
import lms_pb2_grpc
import raft_pb2_grpc


def serve():
    import argparse
    parser = argparse.ArgumentParser(
        description="Input Node ID and Port number for node"
    )
    parser.add_argument("port_number", type=int, help="Port number")
    args = parser.parse_args()
    port = args.port_number

    channel = grpc.insecure_channel(f"localhost:{port-10000}")
    stub = raft_pb2_grpc.RaftServiceStub(channel)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lms_pb2_grpc.add_LMSServicer_to_server(LMSService(port, stub), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"LMS gRPC Server is running on port {port}")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
