from flask import Flask, request, jsonify
from transformers import pipeline

# Initialize Flask app
app = Flask(__name__)

# Load a lightweight GPT-2 model for generating responses
tutoring_model = pipeline('text-generation', model='gpt2')

# Route for handling tutoring queries


@app.route('/tutoring', methods=['POST'])
def tutoring():
    # Parse the incoming JSON request
    data = request.json
    course_name = data.get('course_name', None)
    query = data.get('query', None)

    if not course_name or not query:
        return jsonify({"error": "Both course_name and query are required"}), 400

    # Create a context-aware prompt for the LLM
    prompt = f"Course: {course_name}. Question: {query}. Answer:"

    # Generate a response from the LLM
    response = tutoring_model(
        prompt,
        max_length=500,  # Adjust this as needed
        temperature=0.1,  # Lower value for more focused responses
        top_p=0.9,  # Nucleus sampling to avoid less probable tokens
        repetition_penalty=1.2,  # Penalize repetitive phrases
        num_return_sequences=1  # Generate only one response
    )
    # Return the generated response
    return jsonify({
        "course_name": course_name,
        "query": query,
        "response": response[0]['generated_text']
    })


# Start the server
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002)
