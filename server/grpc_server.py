import os
import sys
import uuid
from functools import wraps

from database import db_connect

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "proto"))
import lms_pb2
import lms_pb2_grpc
from grpc import StatusCode


def authorize(func):
    @wraps(func)
    def wrapper(self, request, context, *args, **kwargs):
        token = request.token

        # Connect to the database and validate token
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id FROM sessions WHERE token = ? AND created_at >= DATETIME('now', '-2 hours')",
            (token,),
        )
        result = cursor.fetchone()

        if result:
            # If token is valid, set user_id and proceed
            user_id = result[0]
            return func(self, request, context, user_id=user_id, *args, **kwargs)
        else:
            # If token is invalid, return failure or raise a gRPC exception
            context.set_code(StatusCode.UNAUTHENTICATED)
            context.set_details("Invalid or expired token.")
            return lms_pb2.GetResponse(status="failure")

    return wrapper


class LMSService(lms_pb2_grpc.LMSServicer):

    def Login(self, request, context):
        conn = db_connect()
        cursor = conn.cursor()

        # Validate username and password (Corrected for SQLite with `?`)
        cursor.execute(
            "SELECT user_id, role FROM users WHERE username = ? AND password = ?",
            (request.username, request.password),
        )
        result = cursor.fetchone()

        if result:
            user_id, role = result
            token = str(uuid.uuid4())  # Generate a session token
            # Corrected for SQLite
            cursor.execute(
                "INSERT INTO sessions (user_id, token) VALUES (?, ?)", (user_id, token)
            )
            conn.commit()
            return lms_pb2.LoginResponse(status="success", token=token)
        else:
            return lms_pb2.LoginResponse(status="failure", token="")

    def Logout(self, request, context):
        conn = db_connect()
        cursor = conn.cursor()

        # Corrected for SQLite
        cursor.execute("DELETE FROM sessions WHERE token = ?", (request.token,))
        conn.commit()

        if cursor.rowcount > 0:
            return lms_pb2.LogoutResponse(status="success")
        else:
            return lms_pb2.LogoutResponse(status="failure")

    @authorize
    def Post(self, request, context, user_id=None):
        post_type = request.type
        content = request.data

        # Save the post in the database
        conn = db_connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO posts (user_id, type, content) VALUES (?, ?, ?)",
            (user_id, post_type, content),
        )
        conn.commit()
        return lms_pb2.PostResponse(status="success")

    @authorize
    def Get(self, request, context, user_id=None):
        request_type = request.type

        conn = db_connect()
        cursor = conn.cursor()

        # Fetch course materials or posts based on request_type
        if request_type == "course material":
            cursor.execute("SELECT material_id, title, content FROM course_materials")
        elif request_type in ["assignment", "query"]:
            cursor.execute(
                "SELECT post_id, content FROM posts WHERE type = ?", (request_type,)
            )
        else:
            lms_pb2.GetResponse(status="failure")

        items = cursor.fetchall()

        # Prepare data items based on the request type
        if request_type == "course material":
            data_items = (
                lms_pb2.DataItem(id=str(item[0]), content=f"{item[1]} - {item[2]}")
                for item in items
            )  # Combine title and content
        else:
            data_items = (
                lms_pb2.DataItem(id=str(item[0]), content=item[1]) for item in items
            )

        return lms_pb2.GetResponse(status="success", data_items=data_items)
