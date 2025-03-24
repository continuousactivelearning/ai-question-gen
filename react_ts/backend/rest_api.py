from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import json
from dotenv import load_dotenv
import os
from datetime import datetime
from transformers import pipeline
import whisper
import spacy
import model 
import torch


# Initialize Flask app
app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

load_dotenv()

# Load spaCy tokenizer
nlp = spacy.load("en_core_web_sm")

# Configure API key from environment variables
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

UPLOAD_FOLDER = "static/uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def get_gemini_model(model_name="gemini-pro"):
    """Helper function to initialize Gemini AI model."""
    try:
        return genai.GenerativeModel(model_name)
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")
        return None
    
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
    

def load_text_file(lines):
    """Load transcript with sentence-level timestamps."""
    sentences = []
    timestamps = []

    for i in range(0, len(lines), 3):
      if i + 1 >= len(lines):  # Skip if not enough lines left
          continue

      time_range = lines[i].strip().split(" --> ")

      # Skip invalid time ranges
      if len(time_range) != 2:
          continue

      try:
          start_time = float(time_range[0])
          end_time = float(time_range[1])
      except ValueError:
          continue

      text = lines[i + 1].strip()

      if text:  # Only add if text is not empty
          sentences.append(text)
          timestamps.append((start_time, end_time))

    tokens = [token.text for sent in sentences for token in nlp(sent)]
    return sentences, tokens, timestamps

@app.route("/upload-audio", methods=["POST"])
def upload_audio():
    """Uploads an audio file."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file uploaded"}), 400
    audio_file = request.files["audio"]
    unique_filename = audio_file.filename
    save_path = os.path.join(UPLOAD_FOLDER, unique_filename)
    audio_file.save(save_path)

    return jsonify({"message": "Audio uploaded successfully", "file_url": f"/static/uploads/{unique_filename}"}), 200

@app.route("/get-files", methods=["GET"])
def get_files():
    """Fetches the list of uploaded audio files."""
    files = [f for f in os.listdir(UPLOAD_FOLDER) if f.endswith(".wav")]
    return jsonify(files)

@app.route("/generateTranscript", methods=['POST'])
def generate_transcript():
    """Generates transcript using OpenAI Whisper model."""
    data = request.get_json()
    filename = data.get('filename')

    if not filename or not os.path.exists(filename):
        return jsonify({"error": "File not found"}), 400

    try:
        #pipe = pipeline("automatic-speech-recognition", model="openai/whisper-large-v3")
        #transcript = pipe(filename, return_timestamps=True)
        whisper_model = whisper.load_model("base")  
        result = whisper_model.transcribe(filename, word_timestamps=False)
        segments = result['segments']

        # Initialize an empty string to accumulate the text
        text_output = ""

        # Loop through the segments and append the formatted text to the text_output variable
        for seg in segments:
            start_time = seg['start']
            end_time = seg['end']
            text = seg['text'].strip()
            text_output += f"{start_time:.2f} --> {end_time:.2f}\n{text}\n\n"
        text_output = text_output.split('\n')
        
        # Model Hyperparameters
        input_dim = 128  # Example input size
        hidden_dim = 256  # Hidden layer size
        model_seg = model.SEGBOT(input_dim, hidden_dim)

        # Load text file and process with sentence-level timestamps
          # Ensure sentence-level transcript format
        sentences, tokens, timestamps = load_text_file(text_output)

        # Example Input (Dummy Tensor)
        x = torch.randn(1, len(tokens), input_dim)  # Batch size of 1, sequence length based on text
        start_units = 0
        output = model_seg(x, start_units)

        # Segment the text and get timestamps
        segments = model_seg.segment_text(sentences, tokens, timestamps, output)

        # Initialize an empty string to accumulate the segmented transcript
        segmented_transcript = ""; err = ''

        # Try to process the segments and handle any errors
        try:
            if segments:
                for i, segment in enumerate(segments):
                    # Extract start time, end time, and text from each segment
                    start_time = segment["start_time"]
                    end_time = segment["end_time"]
                    text = segment["text"]
                    
                    # Append formatted text to the transcript string
                    segmented_transcript += f"Segment {i+1} [{start_time:.2f}s - {end_time:.2f}s]:\n{text}\n\n"
            else:
                err = "No valid segments found. Terminating execution."

        except KeyError as e:
            segmented_transcript = f"KeyError: Missing expected key {e} in one of the segments."
        except Exception as e:
            segmented_transcript = f"An error occurred: {e}"

        # The variable 'segmented_transcript' now contains the segmented transcript


        return jsonify({"transcript": segmented_transcript})
    except Exception as e:
        print(e)
        return jsonify({"error": f"Error generating transcript: {str(e)}"}), 500



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
