
---

# LMS Project

This is a basic Learning Management System (LMS) built using Python, gRPC, and SQLite. The project implements login, logout, post, and get functionalities using gRPC, along with session management through tokens. The system can be interacted with through a command-line interface for both students and instructors.

## Index

- [Project Structure](#project-structure)
- [Requirements](#requirements)
- [Setup Instructions](#setup-instructions)
- [Run the Project](#run-the-project)

## Project Structure

```
/LMS_Project
│
├── /client
│   ├── client.py               # Command-line interface for interacting with the LMS
│   └── grpc_client.py          # gRPC client logic to communicate with the server
│
├── /server
│   ├── grpc_server.py          # Main gRPC server code handling RPC functions
│   ├── lms_server.py           # LMS service implementation with placeholder functions for post, get, etc.
│   ├── database.py             # SQLite database connection and session management logic
│   └── initialize_content.py   # Python script to initialize the LMS course content
│
├── /proto
│   ├── lms.proto               # Protocol buffer file defining gRPC services and messages
│   └── lms_pb2.py              # Auto-generated Python gRPC class (generated using `protoc`)
│   └── lms_pb2_grpc.py         # Auto-generated gRPC server and client classes (generated using `protoc`)
│
└── requirements.txt            # Python dependencies for the project (gRPC, SQLite, etc.)
```


## Requirements

- Python 3.8+

## Setup Instructions

### 1. Clone the repository
```bash
git clone https://github.com/UjjwalAggarwal-1/AOS-Adventure
cd AOS-Adventure
```


### > Run the setup.sh bash file or Follow Steps 2 onwards
* You may create a virtual env and activate it at this step

```
./setup.sh
```
incase the file is not executable, run

```
chmod +x setup.sh
```

### 2. Install Python Dependencies
* You may create a virtual env and activate it at this step

Install the required Python dependencies using `pip`:

```bash
pip install -r requirements.txt
```

### 3. Generate gRPC Code from `lms.proto`

The project uses gRPC for communication. To generate the necessary Python files from the `lms.proto` file, run the following command:

```bash
python -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/lms.proto
```

This will generate `lms_pb2.py` and `lms_pb2_grpc.py` inside the `/proto` directory.

### 4. Initialize Database Content

```bash
python ./server/database.py
python ./server/initialize_content.py
```

This will also insert some dummy course materials into the SQLite database.


## Run the Project

### 1. Run the gRPC Server

Start the gRPC server by running the following command:

```bash
python server/grpc_server.py
```

The server will start listening for requests on port `50051`.

#### To Stop the Server

To stop the gRPC server, simply press `CTRL + C` in the terminal where it is running.

### 2. Run the Client

In a separate terminal, run the client to interact with the LMS:

```bash
python client/client.py
```

The client will provide options for login, posting data, retrieving data, and logging out.

### 3. Using the LMS

Once the client is running, you can:
- Login using the following credentials:
  - username : 
    - instructor1/instructor2/instructor3 for instructor
    - student1/student2/student3/student4/student5 for student
  - password: password123 for all

- Post assignments, course materials, and queries using the `post` option.
- Retrieve course materials and assignments using the `get` option.


