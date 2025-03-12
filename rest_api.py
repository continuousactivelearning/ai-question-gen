from flask import Flask, request, jsonify
import google.generativeai as genai
import json

# Configure your Gemini API key here (if you have one, for better performance)
# If you don't have an API key, the free version will be used, but with limitations.
genai.configure(api_key="AIzaSyBaqZMNKPnzow10rgCfAibLVPbUjy-izM8")

app = Flask(__name__)

def get_gemini_model(model_name="gemini-pro"):
    """Helper function to get a Gemini model instance. Free version used if no API key is provided."""
    try:
        return genai.GenerativeModel(model_name)
    except Exception as e:
        if "API key" in str(e):
            print("Warning: No API key provided. Using free version with limited functionality.")
            return genai.GenerativeModel(model_name) #Still returns a model.
        else:
            raise e #Raise other errors.

def generate_text(model, prompt, params):
    """Generates text using the specified Gemini model and parameters."""
    try:
        response = model.generate_content(prompt, generation_config=genai.GenerationConfig(**params))
        return response.text
    except Exception as e:
        return f"Error: {e}"
    
def generate_structured_text(model, prompt, params, structure):
    """Generates structured text using the specified Gemini model and parameters."""
    try:
        # Construct a prompt that includes the desired structure.
        structured_prompt = f"""
        {prompt}

        Please provide your response in the following JSON format:
        {json.dumps(structure, indent=2)}
        """

        response = model.generate_content(structured_prompt, generation_config=genai.GenerationConfig(**params))
        raw_response = response.text

        # Clean the response by removing markdown code block formatting (```json ... ```).
        if raw_response.startswith('```json') and raw_response.endswith('```'):
            raw_response = raw_response[7:-3].strip()

        # Try to parse the cleaned response as JSON
        try:
            return json.loads(raw_response)  # Attempt to parse the response as JSON
        except json.JSONDecodeError:
            return {"error": "LLM response was not valid JSON.", "raw_response": raw_response}

    except Exception as e:
        return {"error": f"Error: {e}"}


@app.route('/generate', methods=['POST'])
def generate():
    """Endpoint for generating text."""
    data = request.get_json()
    engine = data.get('engine', 'models/gemini-1.5-pro')  # Default to gemini-pro
    prompt = data.get('prompt', '')
    params = data.get('params', {})

    model = get_gemini_model(engine)
    response = generate_text(model, prompt, params)

    return jsonify({'response': response})

@app.route('/generate-structured', methods=['POST'])
def generate_structured():
    """Endpoint for generating structured text."""
    data = request.get_json()
    engine = data.get('engine', 'models/gemini-1.5-pro')
    prompt = data.get('prompt', '')
    params = data.get('params', {})
    structure = data.get('structure', {})

    model = get_gemini_model(engine)
    response = generate_structured_text(model, prompt, params, structure)

    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)