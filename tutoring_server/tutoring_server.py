
import grpc
import os
import sys
from concurrent import futures
from transformers import pipeline
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "proto"))

import tutoring_pb2
import tutoring_pb2_grpc
# Define a shared secret between LMS and Tutoring server
AUTH_TOKEN = "super_secret_token"

# Load the GPT-2 model for generating tutoring responses
tutoring_model = pipeline('text-generation', model='gpt2')


class TutoringService(tutoring_pb2_grpc.TutoringServiceServicer):
    def GetTutoringResponse(self, request, context):
        # Verify the auth_token
        if request.auth_token != AUTH_TOKEN:
            context.abort(grpc.StatusCode.PERMISSION_DENIED,
                          "Unauthorized request")

        course_name = request.course_name
        query = request.query

        print(f"Received a tutoring request for the course: {course_name}")

        # Create a context-aware prompt for the LLM
        prompt = f"In the context of the subject: {course_name}, Please explain in simple terms: {query}"
        print("Prompt:", prompt)
        # Generate a response using GPT-2
        response = tutoring_model(
            prompt,
            max_length=200,
            temperature=0.5,
            top_p=0.9,
            repetition_penalty=1.5,
            num_return_sequences=1
        )

        # Return the generated response
        return tutoring_pb2.TutoringResponse(response=response[0]['generated_text'])


def serve():
    # Start the gRPC server for tutoring
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    tutoring_pb2_grpc.add_TutoringServiceServicer_to_server(
        TutoringService(), server)
    server.add_insecure_port('[::]:50052')
    server.start()
    print("Tutoring gRPC Server is running on port 50052")
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        server.stop(0)


if __name__ == "__main__":
    serve()
