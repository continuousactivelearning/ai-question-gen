---
sidebar_position: 6
---

# API Endpoints

### 1. `GET /`
**Welcome endpoint**  
Returns a basic status message.

---

### 2. `POST /upload-audio`
**Upload audio file** to the server.

- **Body:** `multipart/form-data`
  - `audio_file`: File to upload
- **Response:** 
  - `200 OK` if successful
  - `400 Bad Request` if missing file

---

### 3. `POST /download-youtube-audio`
**Download and extract audio from a YouTube URL**.

- **Body:** JSON
  - `youtube_url`: string (YouTube video link)
- **Response:**
  - `200 OK` if successful
  - `500 Error` if failed

---

### 4. `GET /get-files`
**List all uploaded audio files** available for processing.

- **Response:** JSON array of `.wav` filenames

---

### 5. `POST /generateTranscript`
**Generate a transcript** with segmented text.

- **Body:** JSON
  - `filename`: string (path to `.wav` audio file)
- **Response:** 
  - Transcript text segmented intelligently by model.

---

### 6. `POST /generate`
**Generate free-text content** using Gemini model.

- **Body:** JSON
  - `engine` (optional): Model name
  - `prompt`: Text prompt
  - `params`: Generation parameters (temperature, max tokens, etc.)
- **Response:** Generated text

---

### 7. `POST /generate-structured-bulk`
**Generate multiple structured questions** at once.

- **Body:** JSON
  - `engine`: Model name
  - `prompt`: Content/topic
  - `questionType`: SOL, SML, MTL, or OTL
  - `numQuestions`: Number of questions
  - `params`: Extra model settings
- **Response:** Array of structured questions

---
