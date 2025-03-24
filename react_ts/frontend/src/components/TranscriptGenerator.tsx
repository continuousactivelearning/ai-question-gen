import { useState, useRef } from "react";
import { generateTranscript } from "../api/api";
import QuestionGenerator from "./QuestionGenerator";

interface TranscriptGeneratorProps {
    selectedFile: string;
}

const TranscriptGenerator: React.FC<TranscriptGeneratorProps> = ({ selectedFile }) => {
    const [segments, setSegments] = useState<string[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const audioRef = useRef<HTMLAudioElement | null>(null);

    const getTranscript = async () => {
        if (!selectedFile) return alert("Select a file first.");

        setLoading(true);
        try {
            const response = await generateTranscript(selectedFile);

            if (response.transcript) {
                let transcriptSegments: string[];

                // If transcript is a string, split it by new lines
                if (typeof response.transcript === "string") {
                    transcriptSegments = response.transcript.split("\n").filter(seg => seg.trim() !== "");
                } else if (Array.isArray(response.transcript)) {
                    transcriptSegments = response.transcript;
                } else {
                    alert("Error: Unexpected transcript format.");
                    setSegments([]);
                    return;
                }

                // Filter out segment titles (e.g., "Segment 1 [0.00s - 48.80s]:")
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
            setLoading(false);
        }
    };

    const playAudio = () => {
        if (!selectedFile) {
            alert("Select a file first.");
            return;
        }
        stopAudio();
        const audioUrl = `http://127.0.0.1:5000/static/uploads/${selectedFile}`;
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

    return (
        <div className="transcript-container">
            <div className="button-group">
                <button onClick={getTranscript} disabled={loading}>
                    {loading ? "Generating..." : "Generate Transcript"}
                </button>
                <button onClick={playAudio}>Play Audio</button>
                <button onClick={stopAudio}>Stop Audio</button>
            </div>

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