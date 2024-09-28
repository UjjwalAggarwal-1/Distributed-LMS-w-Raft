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

    def post(self, token, post_type, data, role, input_id):
        
        if post_type == "assignment":
            if role == "student":
                return self.stub.PostAssignment(
                    lms_pb2.PostAssignmentRequest(token=token, content=data, course_id = input_id)
                )
            elif role == "instructor":
                return self.stub.PostAssignmentGrade(
                    lms_pb2.PostAssignmentGradeRequest(token=token, grade=data, assignment_id = input_id)
                )
        elif post_type == "query":
            if role == "student":
                return self.stub.PostQuery(
                    lms_pb2.PostQueryRequest(token=token, content=data, course_id = input_id)
                )
            elif role == "instructor":
                return self.stub.PostQueryReply(
                    lms_pb2.PostQueryReplyRequest(token=token, content=data, query_id = input_id)
                )

    def get(self, token, request_type, course_id):
        return self.stub.Get(lms_pb2.GetRequest(token=token, type=request_type, course_id=course_id))
