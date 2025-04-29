import { useState, useRef, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL;

interface AudioRecorderProps {
    refreshFiles: () => void;
}

const AudioRecorder: React.FC<AudioRecorderProps> = ({ refreshFiles }) => {
    const [recording, setRecording] = useState<boolean>(false);
    const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
    const [youtubeUrl, setYoutubeUrl] = useState<string>("");
    const [extraction, setExtraction] = useState<boolean>(false);
    const [uploadProgress, setUploadProgress] = useState<number>(0);
    const [youtubeProgress, setYoutubeProgress] = useState<number>(0);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const youtubeProgressRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const toggleRecording = async () => {
        if (!recording) {
            try {
                const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                const mediaRecorder = new MediaRecorder(stream);

                mediaRecorder.ondataavailable = (event: BlobEvent) => {
                    if (event.data.size > 0) {
                        setAudioBlob(event.data);
                    }
                };

                mediaRecorder.start();
                mediaRecorderRef.current = mediaRecorder;
                setRecording(true);
            } catch (error) {
                alert("Error accessing microphone. Please check permissions.");
                console.error("Microphone access error:", error);
            }
        } else {
            mediaRecorderRef.current?.stop();
            setRecording(false);
        }
    };

    const uploadRecording = () => {
        if (!audioBlob) {
            alert("No audio recorded yet.");
            return;
        }

        const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
        const filename = `recording_${timestamp}.wav`;

        const formData = new FormData();
        formData.append("audio_file", audioBlob, filename);

        const xhr = new XMLHttpRequest();

        xhr.upload.onprogress = (event: ProgressEvent) => {
            if (event.lengthComputable) {
                const percentComplete = Math.round((event.loaded / event.total) * 100);
                setUploadProgress(percentComplete);
            }
        };

        xhr.onload = () => {
            if (xhr.status === 200) {
                alert("Recording uploaded successfully!");
                refreshFiles();
                setAudioBlob(null);
                setUploadProgress(0);
            } else {
                alert("Error uploading recording.");
            }
        };

        xhr.onerror = () => {
            alert("Error uploading recording.");
        };

        xhr.open("POST", `${API_URL}/upload-audio`);
        xhr.send(formData);
    };

    const handleYoutubeDownload = async () => {
        if (!youtubeUrl) {
            alert("Please enter a valid YouTube URL.");
            return;
        }
        setExtraction(true);
        setYoutubeProgress(0);

        // Fake progress bar animation
        youtubeProgressRef.current = setInterval(() => {
            setYoutubeProgress((prev) => {
                if (prev >= 95) return 95; // Stop at 95%, wait for real response
                return prev + 1;
            });
        }, 100); // 100ms steps

        try {
            const response = await fetch(`${API_URL}/download-youtube-audio`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ youtube_url: youtubeUrl }),
            });

            if (response.ok) {
                alert("YouTube audio extracted and saved successfully!");
                refreshFiles();
                setYoutubeUrl("");
                setYoutubeProgress(100);
            } else {
                alert("Failed to extract audio. Please check the URL.");
            }
        } catch (error) {
            console.error("Error downloading YouTube audio:", error);
            alert("Error downloading audio.");
        } finally {
            setExtraction(false);
            if (youtubeProgressRef.current) {
                clearInterval(youtubeProgressRef.current);
                youtubeProgressRef.current = null;
            }
        }
    };

    useEffect(() => {
        return () => {
            if (youtubeProgressRef.current) {
                clearInterval(youtubeProgressRef.current);
            }
        };
    }, []);

    return (
        <div className="audio-recorder container">
            <h3>Audio Recorder</h3>
            <button onClick={toggleRecording} className="record-button">
                {recording ? "Stop Recording" : "Start Recording"}
            </button>

            {audioBlob && (
                <>
                    <p>Recording ready to upload.</p>
                    <button onClick={uploadRecording}>Upload Recording</button>
                    {uploadProgress > 0 && (
                        <div style={{ marginTop: "10px", width: "100%", maxWidth: "300px" }}>
                            <progress value={uploadProgress} max={100} style={{ width: "100%" }} />
                            <p>{uploadProgress}%</p>
                        </div>
                    )}
                </>
            )}

            <h4>Extract Audio from YouTube</h4>
            <input
                type="text"
                placeholder="Enter YouTube URL"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
            />
            <button onClick={handleYoutubeDownload} disabled={extraction}>
                {extraction ? "Extracting audio..." : "Extract audio"}
            </button>

            {extraction && (
                <div style={{ marginTop: "10px", width: "100%", maxWidth: "300px" }}>
                    <progress value={youtubeProgress} max={100} style={{ width: "100%" }} />
                    <p>{youtubeProgress}%</p>
                </div>
            )}
        </div>
    );
};

export default AudioRecorder;
