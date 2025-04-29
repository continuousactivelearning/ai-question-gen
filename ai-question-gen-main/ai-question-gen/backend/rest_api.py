from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai
import json
from dotenv import load_dotenv
import os
from datetime import datetime
import yt_dlp
from transformers import pipeline
import whisper
#from backend 
import model 
import torch
import subprocess


# Initialize Flask app
app = Flask(__name__)

CORS(app, resources={r"/*": {"origins": "*"}})

load_dotenv()


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
        question_type = structure.get('questionType', '')
        
        # Enhanced prompt with specific formatting instructions
        # Prepare type-specific rules
        otl_rules = '''
        For OTL (Ordering) questions:
        - List items should be in RANDOM order in the question
        - Solution should show the correct order
        - Each step should be clear and distinct
        - Include clear sequence indicators''' if question_type == 'OTL' else ''
        
        mtl_rules = '''
        For MTL (Matching) questions:
        - Ensure pairs are logically related
        - Both lists should have equal number of items
        - Make relationships clear but not obvious''' if question_type == 'MTL' else ''
        
        sml_rules = '''
        For SML (Multiple Select) questions:
        - Include MULTIPLE correct answers (at least 2)
        - Clearly indicate all correct options in solution
        - Each option should be distinct''' if question_type == 'SML' else ''
        
        sol_rules = '''
        For SOL (Single Option) questions:
        - Only one correct answer
        - All options should be plausible
        - Clear explanation for correct/incorrect''' if question_type == 'SOL' else ''
        
        structured_prompt = f"""
        Based on this content: {prompt}

        Generate a question following these STRICT formatting rules:
        1. Replace all placeholder IDs with unique alphanumeric identifiers (e.g., 'opt1', 'opt2', etc.)
        2. Replace 'Rich Text/Markdown' with actual question text
        3. Replace 'Text Value' with meaningful answer options
        4. Ensure all explanations are detailed and helpful
        5. Set appropriate difficulty level (1-5)
        6. Generate realistic parameter values if isParameterized is True

        Additional rules based on question type:
        {otl_rules}
        {mtl_rules}
        {sml_rules}
        {sol_rules}

        The response MUST follow this EXACT JSON structure (replace all placeholders):
        {json.dumps(structure, indent=2)}

        Important:
        - Generate ONLY valid JSON
        - NO text outside JSON structure
        - NO markdown code blocks
        - ALL IDs must be unique
        - ALL placeholder values must be replaced
        """

        response = model.generate_content(structured_prompt, generation_config=genai.GenerationConfig(**params))
        response_text = response.text

        try:
            # Clean and parse the response
            start_index = response_text.find('{')
            end_index = response_text.rfind('}') + 1
            cleaned_response = response_text[start_index:end_index]
            parsed_response = json.loads(cleaned_response)
            
            # Validate the response has no placeholder values
            if any(placeholder in str(parsed_response) for placeholder in [
                "ID of the LOT", "ID of the LOT item", "Text Value", 
                "Rich Text/Markdown", "ID of item in lot"
            ]):
                return {"error": "Response contains placeholder values that were not replaced"}
            
            # Additional validation based on question type
            question_type = parsed_response.get('questionType', '')
            
            if question_type == 'SML':
                # Ensure multiple correct answers for SML
                solution = parsed_response.get('solution', {}).get('SML', {})
                if solution and len(solution.get('itemIds', [])) < 2:
                    return {"error": "SML questions must have at least 2 correct answers"}
                    
            elif question_type == 'OTL':
                # Ensure options are in different order than solution
                lot_items = parsed_response.get('lot', {}).get('lotItems', [])
                solution_orders = parsed_response.get('solution', {}).get('OTL', {}).get('orders', [])
                
                if lot_items and solution_orders:
                    question_order = [item['id'] for item in lot_items]
                    solution_order = sorted(solution_orders, key=lambda x: x['order'])
                    solution_order = [item['itemId'] for item in solution_order]
                    
                    if question_order == solution_order:
                        # Randomly shuffle the lot items
                        import random
                        random.shuffle(lot_items)
                        parsed_response['lot']['lotItems'] = lot_items
                
            return parsed_response
            
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

    tokens = [word for sent in sentences for word in sent.split()]
    return sentences, tokens, timestamps



@app.route("/upload-audio", methods=["POST"])
def upload_audio():
    audio_file = request.files.get("audio_file")
    if audio_file:
        audio_file.save(os.path.join(UPLOAD_FOLDER, audio_file.filename))
        return jsonify({"message": "Audio uploaded successfully!"}), 200
    return jsonify({"error": "No audio file provided."}), 400

@app.route("/", methods=["GET"])
def index():
    return jsonify({"message": "Welcome to the Gemini API!"})

@app.route("/download-youtube-audio", methods=["POST"])
def download_youtube_audio():
    data = request.get_json()
    youtube_url = data.get("youtube_url")

    if not youtube_url:
        return jsonify({"error": "YouTube URL is required"}), 400

    try: 
        # Define yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',  # Download the best audio
            'extractaudio': True,        # Extract audio (no video)
            'audioquality': 0,           # Best quality for audio
            'outtmpl': f'{UPLOAD_FOLDER}/youtube_%(title)s.%(ext)s',  # Use video title for filename
            'quiet': False,              # Show download progress
        }
        
        # Create and run yt-dlp instance to download audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_url, download=True)
            audio_file = ydl.prepare_filename(info_dict)

        output_wav = audio_file.rsplit('.', 1)[0] + '.wav'  # Change the extension to .wav

        # Run FFmpeg conversion command
        subprocess.run(['ffmpeg', '-i', audio_file, output_wav])

        # Optionally, delete the original audio file (if you don't need it)
        import os
        os.remove(audio_file)
        
        return jsonify({"message": "Audio extracted successfully!"}), 200
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": "Failed to extract audio."}), 500

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
    engine = data.get('engine', 'models/gemma-3-27b-it')  # Default to gemini-pro
    prompt = data.get('prompt', '')
    params = data.get('params', {})

    model = get_gemini_model(engine)
    response = generate_text(model, prompt, params)

    return jsonify({'response': response})


@app.route('/generate-structured-bulk', methods=['POST'])
def generate_structured_bulk():
    data = request.get_json()
    engine = data.get('engine', 'models/gemma-3-27b-it')
    prompt = data.get('prompt', '')
    question_type = data.get('questionType', 'MTL')
    num_questions = data.get('numQuestions', 1)
    params = data.get('params', {})
    
    # Get the appropriate structure template
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
    
    structure = structure_types.get(question_type, structure_types["MTL"])
    
    model = get_gemini_model(engine)
    responses = []
    
    # Prepare type-specific rules for bulk generation
    otl_rules = '''
    For OTL (Ordering) questions:
       - List items MUST be in RANDOM order in the question
       - Solution must show the correct sequential order
       - Each step must be clear and distinct
       - Include clear sequence indicators
       - Steps should follow a logical progression''' if question_type == 'OTL' else ''
    
    mtl_rules = '''
    For MTL (Matching) questions:
       - Both lists must have equal number of items
       - Each pair must have a clear, logical relationship
       - Avoid obvious matches
       - Include at least 3 pairs per question''' if question_type == 'MTL' else ''
    
    sml_rules = '''
    For SML (Multiple Select) questions:
       - MUST include at least 2 correct answers
       - Provide 4-6 total options
       - Each option must be distinct
       - Mark ALL correct options in solution''' if question_type == 'SML' else ''
    
    sol_rules = '''
    For SOL (Single Option) questions:
       - Only one correct answer
       - All distractors must be plausible
       - Include clear explanation for why each option is correct/incorrect''' if question_type == 'SOL' else ''
    
    # Create a single comprehensive prompt for all questions
    bulk_prompt = f"""
    Generate {num_questions} distinct questions of type {question_type} based on the following content:
    
    {prompt}
    
    Follow these STRICT rules for each question:
    1. Make each question unique and distinct
    2. Vary difficulty levels (1-5) across questions
    3. For each question:
       - Generate unique alphanumeric IDs for all items (e.g., 'q1_opt1', 'q1_opt2')
       - Create clear, well-formatted question text
       - Provide meaningful answer options (no placeholder text)
       - Write detailed explanations for options
       - If parameterized, use realistic parameter values
    
    Question Type Specific Rules:
    {otl_rules}
    {mtl_rules}
    {sml_rules}
    {sol_rules}
    
    4. Return all questions in a single JSON array
    5. Do not use any placeholder values
    6. Ensure proper JSON formatting
    7. Each question must be complete and self-contained
    """
    
    # Generate all questions in one API call
    response = generate_structured_text(model, bulk_prompt, params, {
        "questions": [structure] * num_questions  # Array of question structures
    })
    
    if "error" in response:
        return jsonify({"error": response["error"]}), 400
    
    # Return the array of questions
    return jsonify({
        "responses": response.get("questions", [])
    })


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5001))
    app.run(host='0.0.0.0', port=port)
