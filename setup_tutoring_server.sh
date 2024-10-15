#!/bin/bash

echo ""
echo "Installing Python dependencies..."
echo ""
pip install -r requirements_tutoring_server.txt ||
pip3 install -r requirements_tutoring_server.txt ||
{ echo "Failed to install dependencies"; exit 1; }

echo ""
echo "Generating gRPC code from tutoring.proto..."
echo ""

# Generate gRPC code for Tutoring
python3 -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/tutoring.proto ||
python -m grpc_tools.protoc -I./proto --python_out=./proto --grpc_python_out=./proto ./proto/tutoring.proto || 
{ echo "Failed to generate gRPC code for tutoring.proto"; exit 1; }

echo "gRPC code generated successfully."
