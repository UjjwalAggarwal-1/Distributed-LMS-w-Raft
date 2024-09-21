import os
import sys

import grpc

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "proto"))
import lms_pb2
import lms_pb2_grpc


class LMSClient:
    def __init__(self):
        channel = grpc.insecure_channel("localhost:50051")
        self.stub = lms_pb2_grpc.LMSStub(channel)

    def login(self, username, password):
        return self.stub.Login(
            lms_pb2.LoginRequest(username=username, password=password)
        )

    def logout(self, token):
        return self.stub.Logout(lms_pb2.LogoutRequest(token=token))

    def post(self, token, post_type, data):
        return self.stub.Post(
            lms_pb2.PostRequest(token=token, type=post_type, data=data)
        )

    def get(self, token, request_type):
        return self.stub.Get(lms_pb2.GetRequest(token=token, type=request_type))
