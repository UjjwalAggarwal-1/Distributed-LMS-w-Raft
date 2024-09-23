import os
import sys
import uuid
from database import db_connect

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "proto"))
import lms_pb2
import lms_pb2_grpc


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

    def Post(self, request, context):
        # Placeholder for post logic
        token = request.token
        post_type = request.type
        content = request.data

        # Validate token and post data (Corrected for SQLite)
        conn = db_connect()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM sessions WHERE token = ?", (token,))
        result = cursor.fetchone()

        if result:
            user_id = result[0]
            cursor.execute(
                "INSERT INTO posts (user_id, type, content) VALUES (?, ?, ?)",
                (user_id, post_type, content),
            )  # Corrected for SQLite
            conn.commit()
            return lms_pb2.PostResponse(status="success")
        else:
            return lms_pb2.PostResponse(status="failure")

    def Get(self, request, context):
        token = request.token
        request_type = request.type

        conn = db_connect()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM sessions WHERE token = ?", (token,))
        result = cursor.fetchone()

        if result:
            if request_type == "course material":
                # Fetch both title and content for course materials
                cursor.execute(
                    "SELECT material_id, title, content FROM course_materials"
                )
            else:
                cursor.execute(
                    "SELECT post_id, content FROM posts WHERE type = ?", (request_type,)
                )

            items = cursor.fetchall()
            
            if request_type == "course material":
                data_items = [
                    lms_pb2.DataItem(id=str(item[0]), content=f"{item[1]} - {item[2]}")
                    for item in items
                ]  # Combine title and content
            else:
                data_items = [
                    lms_pb2.DataItem(id=str(item[0]), content=item[1]) for item in items
                ]

            return lms_pb2.GetResponse(status="success", data_items=data_items)
        else:
            return lms_pb2.GetResponse(status="failure", data_items=[])
