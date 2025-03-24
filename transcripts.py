import whisper
import os
import re

# Function to get the base directory dynamically (works across devices)
def get_base_path():
    return os.path.dirname(os.path.realpath(__file__))

# Load Whisper model
model = whisper.load_model("base")  # Try "medium" or "large" for better accuracy

# Path to the downloaded audio
audio_file = os.path.join(get_base_path(), 'audio.mp3')  # Use the dynamic path to the audio file

# Transcribe the audio file using Whisper
result = model.transcribe(audio_file, word_timestamps=True)

# Function to split text into sentences using punctuation
def split_sentences_with_timestamps(segments):
    sentences = []
    current_sentence = []
    start_time, end_time = None, None

    for segment in segments:
        words = segment["words"]
        for word in words:
            if start_time is None:
                start_time = word["start"]
            end_time = word["end"]
            current_sentence.append(word["word"])

            # Check if sentence-ending punctuation is found
            if re.search(r'[.!?]', word["word"].strip()):
                sentence_text = " ".join(current_sentence).strip()
                if sentence_text:
                    sentences.append({
                        "text": sentence_text,
                        "start": start_time,
                        "end": end_time
                    })
                # Reset for next sentence
                current_sentence = []
                start_time, end_time = None, None

    # Add remaining sentence if any
    if current_sentence:
        sentence_text = " ".join(current_sentence).strip()
        if sentence_text:
            sentences.append({
                "text": sentence_text,
                "start": start_time,
                "end": end_time
            })

    return sentences

# Split sentences with proper punctuation
sentence_segments = split_sentences_with_timestamps(result["segments"])

# Save sentence-level transcript with proper sentence boundaries
output_path = os.path.join(get_base_path(), "sentence_timestamps.txt")  # Save dynamically in the base directory

with open(output_path, "w") as f:
    for seg in sentence_segments:
        start_time = seg['start']
        end_time = seg['end']
        text = seg['text']
        f.write(f"{start_time:.2f} --> {end_time:.2f}\n{text}\n\n")

print(f"Sentence-level transcript with accurate timestamps saved successfully to {output_path}")

