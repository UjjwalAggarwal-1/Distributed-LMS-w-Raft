import sqlite3


def initialize_course_content():
    # Connect to SQLite database (this will create the file if it doesn't exist)
    conn = sqlite3.connect("lms_db.sqlite")
    cursor = conn.cursor()

    # Check if there is already course content in the table
    cursor.execute("SELECT COUNT(*) FROM course_materials")
    material_count = cursor.fetchone()[0]

    if material_count == 0:
        # Insert initial course materials
        course_materials = [
            ("Course Syllabus", "This is the syllabus for the course."),
            ("Assignment 1", "Complete the following assignment and upload it."),
        ]
        cursor.executemany(
            "INSERT INTO course_materials (title, content) VALUES (?, ?);",
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
