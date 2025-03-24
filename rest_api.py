from flask import Flask, request, jsonify
import google.generativeai as genai
import json

# Configure your Gemini API key here (if you have one, for better performance)
# If you don't have an API key, the free version will be used, but with limitations.
genai.configure(api_key="AIzaSyDDM9X4KituIYCukvIK-b-_YN76s611hRc")

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
    try:
        structured_prompt = f"""
        {prompt}

        Please provide your response in the following JSON format. Ensure the response is valid JSON. Do not include any text outside of the JSON structure. Do not include any markdown code blocks.
        {json.dumps(structure, indent=2)}
        """

        response = model.generate_content(structured_prompt, generation_config=genai.GenerationConfig(**params))
        response_text = response.text

        try:
            start_index = response_text.find('{')
            end_index = response_text.rfind('}') + 1
            cleaned_response = response_text[start_index:end_index]
            return json.loads(cleaned_response)
        except (ValueError, json.JSONDecodeError, IndexError) as e:
            return {"error": "LLM response was not valid JSON.", "raw_response": response_text, "parsing_error": str(e)}

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
    data = request.get_json()
    engine = data.get('engine', 'models/gemini-1.5-pro')
    prompt = data.get('prompt', '')
    params = data.get('params', {})
    structure_types = {
        "SOL": {
            "questionType": "SOL",
            "questionText": "Rich Text/Markdown",
            "hintText": "Rich Text/ Markdown",
            "difficulty": 2,
            "isParameterized": True,
            "parameters": {
                "parameterName": "a",
                "allowedValued": ["2", "3", "9"]
            },
            "lot": {
                "lotId": "ID of the LOT",
                "lotItems": [
                    {
                        "id": "ID of the LOT item",
                        "lotItemText": "Text Value",
                        "explaination": "Explaination as why this option is correct/incorrect"
                    },
                    {
                        "id": "ID of the LOT item",
                        "lotItemText": "Text Value",
                        "explaination": "Explaination as why this option is correct/incorrect"
                    }
                ]
            },
            "solution": {
                "SOL": {
                    "itemId": "ID of the solution item in the lot"
                }
            },
            "metaDetails": {
                "isStudentGenerated": True,
                "isAIGenerated": False
            },
            "timeLimit": 300,
            "points": 20
        },
        "SML": {
            "questionType": "SML",
            "questionText": "Rich Text/Markdown",
            "hintText": "Rich Text/ Markdown",
            "difficulty": 2,
            "isParameterized": True,
            "parameters": {
                "parameterName": "a",
                "allowedValued": ["2", "3", "9"]
            },
            "lot": {
                "lotItems": [
                    {
                        "id": "ID of the LOT item",
                        "lotItemText": "Text Value",
                        "explaination": "Explaination as why this option is correct/incorrect"
                    },
                    {
                        "id": "ID of the LOT item",
                        "lotItemText": "Text Value",
                        "explaination": "Explaination as why this option is correct/incorrect"
                    }
                ]
            },
            "solution": {
                "SML": {
                    "itemIds": [
                        "ID of the solution item in the lot",
                        "ID of the solution item in the lot"
                    ]
                }
            },
            "metaDetails": {
                "isStudentGenerated": True,
                "isAIGenerated": False
            },
            "timeLimit": 300,
            "points": 20
        },
        "MTL": {
            "questionType": "MTL",
            "questionText": "Rich Text/Markdown",
            "hintText": "Rich Text/ Markdown",
            "difficulty": 2,
            "isParameterized": True,
            "parameters": {
                "parameterName": "a",
                "allowedValued": ["2", "3", "9"]
            },
            "lots": [
                {
                    "lotId": "ID of the LOT",
                    "lotItems": [
                        {
                            "id": "ID of the LOT item",
                            "lotItemText": "Text Value"
                        },
                        {
                            "id": "ID of the LOT item",
                            "lotItemText": "Text Value"
                        }
                    ]
                },
                {
                    "lotId": "ID of the LOT",
                    "lotItems": [
                        {
                            "id": "ID of the LOT item",
                            "lotItemText": "Text Value"
                        },
                        {
                            "id": "ID of the LOT item",
                            "lotItemText": "Text Value"
                        }
                    ]
                }
            ],
            "solution": {
                "MTL": {
                    "matches": [
                        {
                            "itemIds": [
                                "ID of item in lot 1",
                                "ID of item in lot 2"
                            ]
                        },
                        {
                            "itemIds": [
                                "ID of item in lot 1",
                                "ID of item in lot 2"
                            ]
                        }
                    ]
                }
            },
            "metaDetails": {
                "isStudentGenerated": True,
                "isAIGenerated": False
            },
            "timeLimit": 300,
            "points": 20
        },
        "OTL": {
            "questionType": "OTL",
            "questionText": "Rich Text/Markdown",
            "hintText": "Rich Text/ Markdown",
            "difficulty": 2,
            "isParameterized": True,
            "parameters": {
                "parameterName": "a",
                "allowedValued": ["2", "3", "9"]
            },
            "lot": {
                "lotId": "ID of the LOT",
                "lotItems": [
                    {
                        "id": "ID of the LOT item",
                        "lotItemText": "Text Value"
                    },
                    {
                        "id": "ID of the LOT item",
                        "lotItemText": "Text Value"
                    }
                ]
            },
            "solution": {
                "OTL": {
                    "orders": [
                        {
                            "itemId": "ID of the solution item in the lot",
                            "order": 1
                        },
                        {
                            "itemId": "ID of the solution item in the lot",
                            "order": 2
                        },
                        {
                            "itemId": "ID of the solution item in the lot",
                            "order": 3
                        }
                    ]
                }
            },
            "metaDetails": {
                "isStudentGenerated": True,
                "isAIGenerated": False
            },
            "timeLimit": 300,
            "points": 20
        }
    }

    question_type = data.get("questionType", "MTL")
    structure = structure_types.get(question_type, structure_types["MTL"])

    model = get_gemini_model(engine)
    response = generate_structured_text(model, prompt, params, structure)

    return jsonify(response)

    

if __name__ == '__main__':
    app.run(debug=True)
