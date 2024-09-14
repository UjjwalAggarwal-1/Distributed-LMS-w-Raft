import mysql.connector

def db_connect():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root_password",  # Replace with your MySQL password
        database="lms_db"
    )
