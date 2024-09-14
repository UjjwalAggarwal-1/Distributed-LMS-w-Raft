CREATE DATABASE IF NOT EXISTS lms_db;
USE lms_db;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(100) NOT NULL,
    role ENUM('student', 'instructor') NOT NULL
);

-- Create session table
CREATE TABLE IF NOT EXISTS sessions (
    session_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    token VARCHAR(255) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP DEFAULT DATE_ADD(CURRENT_TIMESTAMP, INTERVAL 1 DAY)
);

-- Create posts table (assignments, queries)
CREATE TABLE IF NOT EXISTS posts (
    post_id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT,
    type ENUM('assignment', 'query') NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(user_id)
);

-- Create course materials table
CREATE TABLE IF NOT EXISTS course_materials (
    material_id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial data for instructors and students
INSERT INTO users (username, password, role) 
VALUES ('instructor1', 'password123', 'instructor'),
       ('student1', 'password123', 'student'),
       ('student2', 'password123', 'student');

-- Insert initial course materials
INSERT INTO course_materials (title, content) 
VALUES 
('Course Syllabus', 'This is the syllabus for the course.'),
('Assignment 1', 'Submit assignment by next week.');
