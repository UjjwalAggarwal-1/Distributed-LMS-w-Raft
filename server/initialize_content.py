import mysql.connector

def initialize_course_content():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='root_password',
        database='lms_db'
    )
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM course_materials")
    material_count = cursor.fetchone()[0]

    if material_count == 0:
        course_materials = [
            ("Course Syllabus", "This is the syllabus for the course."),
            ("Assignment 1", "Complete the following assignment and upload it.")
        ]
        cursor.executemany("INSERT INTO course_materials (title, content) VALUES (%s, %s);", course_materials)
        conn.commit()
        print("Course content initialized.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    initialize_course_content()
