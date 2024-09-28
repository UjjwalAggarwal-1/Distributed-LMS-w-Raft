import sqlite3
from database import db_connect

def initialize_course_content():
    # Connect to SQLite database (this will create the file if it doesn't exist)
    conn = db_connect()
    cursor = conn.cursor()

    # Check if there is already course content in the table
    cursor.execute("SELECT COUNT(*) FROM courses")
    material_count = cursor.fetchone()[0]

    if material_count == 0:
        # Insert initial course materials
        course_materials = [
            ("Advanced Operating Systems", "This is the syllabus for the course."),
            ("Operating Systems", "Read the following modules and understand it all."),
            ("Advanced Computer Networks", "This is the syllabus for the course. Read the following information."),
            ("Computer Networks", "Read the following modules and understand it all."),
        ]
        cursor.executemany(
            "INSERT INTO courses (title, content) VALUES (?, ?);",
            course_materials,
        )
        conn.commit()
        print("Course content initialized.")
    else:
        print("Course content already exists.")

    # Check if there are already users in the table
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    if user_count == 0:
        # Insert initial users (3 instructor and 5 students)
        users = [
            ("instructor1", "password123", "instructor"),
            ("instructor2", "password123", "instructor"),
            ("instructor3", "password123", "instructor"),
            ("student1", "password123", "student"),
            ("student2", "password123", "student"),
            ("student3", "password123", "student"),
            ("student4", "password123", "student"),
            ("student5", "password123", "student"),
            ("LLM", "234ad$sf23!4adf34", "LLM"),
        ]
        cursor.executemany(
            "INSERT INTO users (username, password, role) VALUES (?, ?, ?);", users
        )
        conn.commit()
        print("Users initialized.")
    else:
        print("Users already exist.")

    cursor.close()
    conn.close()


if __name__ == "__main__":
    initialize_course_content()
