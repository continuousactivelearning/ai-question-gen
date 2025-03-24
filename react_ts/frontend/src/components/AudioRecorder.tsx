import { useState, useRef } from "react";
import { uploadAudio } from "../api/api";

interface AudioRecorderProps {
    refreshFiles: () => void;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({ refreshFiles }) => {
    const [isRecording, setIsRecording] = useState(false);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const [filename, setFilename] = useState<string>("");
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const [audioChunks, setAudioChunks] = useState<Blob[]>([]);

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            setAudioChunks([]);

            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    setAudioChunks((prev) => [...prev, event.data]);
                }
            };

            mediaRecorder.onstop = () => {
                const audioBlob = new Blob(audioChunks, { type: "audio/wav" });
                const audioUrl = URL.createObjectURL(audioBlob);
                setAudioUrl(audioUrl);
            };

            mediaRecorder.start();
            setIsRecording(true);
        } catch (error) {
            console.error("Error accessing microphone:", error);
            alert("Microphone access is required for recording.");
        } 
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            setIsRecording(false);
        }
    };

    const upload = async () => {
        if (audioChunks.length === 0) {
            alert("No audio recorded!");
            return;
        }

        if (!filename.trim()) {
            alert("Please enter a filename before uploading.");
            return;
        }

        const audioBlob = new Blob(audioChunks, { type: "audio/wav" });

        try {
            const response = await uploadAudio(audioBlob, filename.trim());

            if (response.error) {
                alert(`Upload failed: ${response.error}`);
            } else {
                alert(response.message);
                refreshFiles();
                setAudioUrl(null);
                setAudioChunks([]);
                setFilename(""); 
            }
        } catch (error) {
            console.error("Error uploading:", error);
            alert("An error occurred while uploading the file.");
        }
    };

    return (
        <div>
            <h2>Audio Recorder</h2>
            <input
                type="text"
                placeholder="Filename"
                value={filename}
                onChange={(e) => setFilename(e.target.value)}
            />
            <button onClick={startRecording} disabled={isRecording}>{isRecording ? "Recording..." : "Start Recording"}</button>
            <button onClick={stopRecording} disabled={!isRecording}>Stop</button>
            <button onClick={upload} disabled={!audioUrl}>Upload</button>
            {/*{audioUrl && <audio controls src={audioUrl}></audio>}*/}

        </div>
    );
};

export default AudioRecorder;
