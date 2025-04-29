import { useState, useRef, useEffect } from "react";
import { generateTranscript } from "../api/api";
import QuestionGenerator from "./QuestionGenerator";

const API_URL = import.meta.env.VITE_API_URL;

interface TranscriptGeneratorProps {
    selectedFile: string;
}

const TranscriptGenerator: React.FC<TranscriptGeneratorProps> = ({ selectedFile }) => {
    const [segments, setSegments] = useState<string[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [progress, setProgress] = useState<number>(0);
    const audioRef = useRef<HTMLAudioElement | null>(null);
    const progressIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const startFakeProgress = () => {
        setProgress(0);
        progressIntervalRef.current = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 95) return 95; // Cap at 95% until actual finish
                return prev + 1;
            });
        }, 100);
    };

    const stopFakeProgress = () => {
        if (progressIntervalRef.current) {
            clearInterval(progressIntervalRef.current);
            progressIntervalRef.current = null;
        }
        setProgress(100);
        setTimeout(() => setProgress(0), 800); // Reset after showing 100%
    };

    const getTranscript = async () => {
        if (!selectedFile) return alert("Select a file first.");

        setLoading(true);
        startFakeProgress();

        try {
            const response = await generateTranscript(selectedFile);

            if (response.transcript) {
                let transcriptSegments: string[];

                if (typeof response.transcript === "string") {
                    transcriptSegments = response.transcript.split("\n").filter(seg => seg.trim() !== "");
                } else if (Array.isArray(response.transcript)) {
                    transcriptSegments = response.transcript;
                } else {
                    alert("Error: Unexpected transcript format.");
                    setSegments([]);
                    return;
                }

                const filteredSegments = transcriptSegments.filter(
                    (seg) => !/^Segment \d+ \[\d{1,3}\.\d{2}s - \d{1,3}\.\d{2}s\]:/.test(seg)
                );

                setSegments(filteredSegments);
            } else {
                alert("Error generating transcript.");
            }
        } catch (error) {
            console.error("Transcript error:", error);
            alert("An error occurred while generating the transcript.");
        } finally {
            stopFakeProgress();
            setLoading(false);
        }
    };

    const playAudio = () => {
        if (!selectedFile) {
            alert("Select a file first.");
            return;
        }
        stopAudio();
        const audioUrl = `${API_URL}/static/uploads/${selectedFile}`;
        const newAudio = new Audio(audioUrl);
        newAudio.play();
        audioRef.current = newAudio;
    };

    const stopAudio = () => {
        if (audioRef.current) {
            audioRef.current.pause();
            audioRef.current.currentTime = 0;
            audioRef.current = null;
        }
    };

    useEffect(() => {
        return () => {
            if (progressIntervalRef.current) {
                clearInterval(progressIntervalRef.current);
            }
        };
    }, []);

    return (
        <div className="transcript-container">
            <div className="button-group">
                <button onClick={getTranscript} disabled={loading}>
                    {loading ? "Generating..." : "Generate Transcript"}
                </button>
                <button onClick={playAudio}>Play Audio</button>
                <button onClick={stopAudio}>Stop Audio</button>
            </div>

            {loading && (
                <div style={{ marginTop: "10px", width: "100%", maxWidth: "300px" }}>
                    <progress value={progress} max={100} style={{ width: "100%" }} />
                    <p>{progress}%</p>
                </div>
            )}

            <div className="transcript-section">
                <h3>Transcript Segments:</h3>
                {segments.length > 0 ? (
                    <ul className="segment-list">
                        {segments.map((seg, idx) => (
                            <li key={idx}>{seg}</li>
                        ))}
                    </ul>
                ) : (
                    <p>No segments available. Generate a transcript first.</p>
                )}
            </div>

            {segments.length > 0 && <QuestionGenerator segments={segments} />}
        </div>
    );
};

export default TranscriptGenerator;

