---
sidebar_position: 5
---
# Question generation
# Concepts

## Overview
This project is an AI-powered **Question Generation** service based on **audio files** or **custom prompts**.  
It uses:
- **Flask** backend
- **Google Gemini AI** for text generation
- **OpenAI Whisper** for speech-to-text transcription
- **SEGBOT segmentation model** for smarter sentence segmentation

## Key Components
### 1. Gemini Text Generation
- Google Gemini API is used to generate normal and structured questions.
- Structured formats are enforced (e.g., matching, ordering, multiple-choice).

### 2. Whisper Speech Recognition
- Whisper model transcribes uploaded audio files into text with timestamps.
- Text is segmented into coherent parts for better question generation.

### 3. Audio Handling
- Audio can be uploaded manually or extracted from YouTube URLs.
- Audio is converted into `.wav` format for processing.

### 4. Question Types
- **SOL** - Single Option (MCQ with one correct answer)
- **SML** - Select Multiple (MCQ with multiple correct answers)
- **MTL** - Matching (match two related lists)
- **OTL** - Ordering (arrange items in the correct order)

### 5. Structured Bulk Generation
- Allows generating multiple structured questions in a single API call.
- Ensures diversity and strict formatting.

---
