
from grpc import StatusCode
import grpc
import os
import sqlite3
import sys
import uuid
from functools import wraps
from database import db_connect
from concurrent import futures
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "proto"))

import tutoring_pb2_grpc
import tutoring_pb2
import lms_pb2_grpc
import lms_pb2

def db_execute(sql_query, args):
    try:
        conn = db_connect()
        cursor = conn.cursor()

        cursor.execute(sql_query, args)

        conn.commit()
        return "success"

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")
        return str(e)

    finally:
        cursor.close()
        conn.close()


def authorize(func):
    @wraps(func)
    def wrapper(self, request, context, *args, **kwargs):
        token = request.token
        # Connect to the database and validate token
        conn = db_connect()
        try:
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
        except Exception as e:
            print(e)
            context.set_code(StatusCode.INTERNAL)
            context.set_details("Internal server error.")
            return lms_pb2.GetResponse(status="failure")
        finally:
            cursor.close()
            conn.close()

    return wrapper


def authorize_role(required_role):
    def decorator(func):
        @wraps(func)
        @authorize  # Wrap with authorize to first validate token
        def wrapper(self, request, context, *args, **kwargs):
            user_id = kwargs.get("user_id")
            if not user_id:
                # If user_id is missing from authorization, return failure
                context.set_code(StatusCode.UNAUTHENTICATED)
                context.set_details("Authorization failed.")
                return lms_pb2.GetResponse(status="failure")

            # Connect to the database and check if the user has the required role
            conn = db_connect()
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT role FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                if result and result[0] == required_role:
                    # If user has the required role, proceed to the original function
                    return func(self, request, context, *args, **kwargs)
                else:
                    # If user does not have the required role, return unauthorized
                    context.set_code(StatusCode.PERMISSION_DENIED)
                    context.set_details(
                        f"User does not have the required role: {required_role}"
                    )
                    return lms_pb2.GetResponse(status="failure")
            except Exception as e:
                print(e)
                context.set_code(StatusCode.INTERNAL)
                context.set_details("Internal server error.")
                return lms_pb2.GetResponse(status="failure")
            finally:
                cursor.close()
                conn.close()

        return wrapper

    return decorator


class LMSService(lms_pb2_grpc.LMSServicer):
    def get_ai_response(self, course_name, query):
        try:
            print("Connecting to Tutoring Server...")

            # Connect to the Tutoring Server on port 50052
            channel = grpc.insecure_channel('localhost:50052')
            stub = tutoring_pb2_grpc.TutoringServiceStub(channel)

            # Make the request to the tutoring server
            response = stub.GetTutoringResponse(
                tutoring_pb2.TutoringRequest(
                    course_name=course_name, query=query, auth_token="super_secret_token"
                )
            )
            return response.response

        except grpc.RpcError as e:
            print(f"Failed to connect to Tutoring Server: {e}")
            return None
        except Exception as ex:
            print(f"Unexpected error: {ex}")
            return None


    def Login(self, request, context):
        conn = db_connect()
        cursor = conn.cursor()

        # Validate username and password
        cursor.execute(
            "SELECT user_id, role FROM users WHERE username = ? AND password = ?",
            (request.username, request.password),
        )
        result = cursor.fetchone()

        if result:
            user_id, role = result
            token = str(uuid.uuid4())  # Generate a session token

            cursor.execute(
                "INSERT INTO sessions (user_id, token) VALUES (?, ?)", (user_id, token)
            )
            conn.commit()
            return lms_pb2.LoginResponse(status="success", token=token, role=role)
        else:
            return lms_pb2.LoginResponse(status="failure")

    @authorize
    def Logout(self, request, context, *args, **kwargs):
        conn = db_connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sessions WHERE token = ?",
                       (request.token,))
        conn.commit()
        cursor.close()
        conn.close()

        if cursor.rowcount > 0:
            return lms_pb2.LogoutResponse(status="success")
        else:
            return lms_pb2.LogoutResponse(status="failure")

    @authorize_role("student")
    def PostAssignment(self, request, context, user_id=None, *args, **kwargs):

        content = request.content
        course_id = request.course_id

        # Save the post in the database
        res = db_execute(
            """
            INSERT INTO assignments (user_id, course_id, content)
            VALUES (?, ?, ?)
            """,
            (user_id, course_id, content),
        )
        return lms_pb2.PostResponse(status=res)

    @authorize_role("instructor")
    def PostAssignmentGrade(self, request, context, user_id=None):

        grade = request.grade
        assignment_id = request.assignment_id

        # Save the post in the database
        res = db_execute(
            """
            UPDATE assignments SET grade=? WHERE assignment_id=?
            """,
            (grade, assignment_id),
        )

        return lms_pb2.PostResponse(status=res)

    def PostQuery(self, request, context, user_id=None):

        content = request.content
        course_id = request.course_id
        is_ai = request.is_ai

        # Step 1: Fetch the course name based on course_id
        conn = db_connect()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT title FROM courses WHERE course_id = ?",
            (course_id,)
        )
        course_name_row = cursor.fetchone()
        if not course_name_row:
            context.abort(grpc.StatusCode.NOT_FOUND, "Course not found")

        course_name = course_name_row[0]

        # Step 2: Handle AI query
        if is_ai:

            cursor.execute(
                "SELECT user_id, role FROM users WHERE username = LLM"
            )
            llm_id = cursor.fetchone()
            # Call the Tutoring Server with the course name and query
            ai_response = self.get_ai_response(course_name, content)
            if not ai_response:
                context.abort(grpc.StatusCode.UNAVAILABLE, "AI tutoring service is unavailable. Please try again later.")

            # Save the AI response as the reply to the query
            cursor.execute(
                """
                INSERT INTO queries (user_id, course_id, content, reply, replied_at, replier_id)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
                """,
                (user_id, course_id, content, ai_response, llm_id[0]),
            )
        else:
            # Save a regular query without a reply
            cursor.execute(
                """
                INSERT INTO queries (user_id, course_id, content)
                VALUES (?, ?, ?)
                """,
                (user_id, course_id, content),
            )

        conn.commit()
        cursor.close()
        conn.close()

        return lms_pb2.PostResponse(status="success")


    @authorize_role("instructor")
    def PostQueryReply(self, request, context, user_id=None):

        reply = request.content
        query_id = request.query_id

        # Save the post in the database
        conn = db_connect()
        cursor = conn.cursor()

        cursor.execute(
            """
            UPDATE queries set replier_id=?, reply=?, replied_at=CURRENT_TIMESTAMP
            WHERE query_id = ?
            """,
            (user_id, reply, query_id),
        )

        conn.commit()
        cursor.close()
        conn.close()
        return lms_pb2.PostResponse(status="success")

    @authorize
    def Get(self, request, context, user_id=None):
        request_type = request.type
        course_id = request.course_id

        conn = db_connect()
        cursor = conn.cursor()

        # Fetch course materials or posts based on request_type
        if request_type == "course material":
            cursor.execute(
                "SELECT course_id, title, content FROM courses where course_id = ?", (course_id,))
        elif request_type == "assignment":
            cursor.execute(
                "SELECT assignment_id, user_id, content, grade FROM assignments where course_id = ?",
                (course_id,),
            )
        elif request_type == "query":
            cursor.execute(
                "SELECT query_id, user_id, content, reply, replier_id FROM queries where course_id = ?",
                (course_id,),
            )
        else:
            lms_pb2.GetResponse(status="failure")

        items = cursor.fetchall()

        # Prepare data items based on the request type
        if request_type == "course material":
            data_items = (
                lms_pb2.DataItem(
                    id=str(item[0]), content=f"{item[1]} - {item[2]}")
                for item in items
            )  # Combine title and content
        elif request_type == "query":
            data_items = (
                lms_pb2.DataItem(id=str(item[0]), content=f"{item[1]} asked {item[2]} and got {item[3]} from {item[4]}") for item in items
            )
        else:
            data_items = (
                lms_pb2.DataItem(id=str(item[0]), content=f"{item[1]} submitted {item[2]} and got {item[3]}") for item in items
            )

        return lms_pb2.GetResponse(status="success", data_items=data_items)
