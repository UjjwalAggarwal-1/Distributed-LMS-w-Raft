import os
import sys
from concurrent import futures

import grpc
from grpc_server import LMSService

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "proto"))
import lms_pb2_grpc


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    lms_pb2_grpc.add_LMSServicer_to_server(LMSService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    print("LMS gRPC Server is running on port 50051")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
