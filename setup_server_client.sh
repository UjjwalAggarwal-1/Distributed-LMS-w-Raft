#!/bin/bash

echo ""
echo "Installing Python dependencies..."
echo ""
pip install -r requirements_server_client.txt ||
pip3 install -r requirements_server_client.txt ||
{ echo "Failed to install dependencies"; exit 1; }

echo ""
echo "Generating gRPC code from lms.proto and raft.proto..."
echo ""

# Generate gRPC code for LMS
python3 -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/lms.proto ||
python -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/lms.proto || 
{ echo "Failed to generate gRPC code for lms.proto"; exit 1; }

# Generate gRPC code for Raft
python3 -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/raft.proto ||
python -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/raft.proto || 
{ echo "Failed to generate gRPC code for lms.proto"; exit 1; }

echo "gRPC code generated successfully."


echo ""
echo "Initializing database content..."
echo ""

rm lms_db.sqlite

python3 ./server/database.py ||
python ./server/database.py ||
{ echo "Failed to setup database"; exit 1; }

python3 ./server/initialize_content.py || 
python ./server/initialize_content.py ||
{ echo "Failed to initialize content"; exit 1; }

mkdir logs