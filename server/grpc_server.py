import os
import sqlite3
import sys
import uuid
from functools import wraps

from database import db_connect

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "proto"))
import lms_pb2
import lms_pb2_grpc
from grpc import StatusCode


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
                cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
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
    def Logout(self, request, context):
        conn = db_connect()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM sessions WHERE token = ?", (request.token,))
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

        grade = request.content
        assignment_id = request.course_id

        # Save the post in the database
        res = db_execute(
            """
            UPDATE assignments SET grade=? WHERE assignment_id=?
            """,
            (grade, assignment_id),
        )

        return lms_pb2.PostResponse(status=res)

    @authorize_role("student")
    def PostQuery(self, request, context, user_id=None):

        content = request.content
        course_id = request.course_id

        # Save the post in the database
        conn = db_connect()
        cursor = conn.cursor()

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
    def PostQueryResponse(self, request, context, user_id=None):

        reply = request.content
        query_id = request.course_id

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

        conn = db_connect()
        cursor = conn.cursor()

        # Fetch course materials or posts based on request_type
        if request_type == "course material":
            cursor.execute("SELECT course_id, title, content FROM courses")
        elif request_type == "assignment":
            cursor.execute(
                "SELECT assignment_id, content FROM assignments"
            )
        elif request_type == "query":
            cursor.execute(
                "SELECT query_id, content FROM queries"
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
