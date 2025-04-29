import { useState, useRef, useEffect } from "react";

const API_URL = import.meta.env.VITE_API_URL;

interface QuestionGeneratorProps {
    segments: string[];
}

const QuestionGenerator: React.FC<QuestionGeneratorProps> = ({ segments }) => {
    const [questionType, setQuestionType] = useState("MTL");
    const [selectedSegment, setSelectedSegment] = useState<string>("");
    const [numQuestions, setNumQuestions] = useState<number>(1);
    const [responses, setResponses] = useState<any[]>([]);
    const [loading, setLoading] = useState<boolean>(false);
    const [progress, setProgress] = useState<number>(0);
    const progressIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const startFakeProgress = () => {
        setProgress(0);
        progressIntervalRef.current = setInterval(() => {
            setProgress((prev) => {
                if (prev >= 95) return 95;
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
        setTimeout(() => setProgress(0), 800); // Reset after a short delay
    };

    const generateQuestions = async () => {
        if (!selectedSegment || numQuestions < 1) {
            alert("Please select a valid segment and number of questions.");
            return;
        }

        setLoading(true);
        setResponses([]);
        startFakeProgress();

        try {
            const response = await fetch(`${API_URL}/generate-structured-bulk`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: selectedSegment,
                    questionType,
                    numQuestions,
                    params: {}
                })
            });

            const data = await response.json();

            if (data.responses && Array.isArray(data.responses)) {
                setResponses(data.responses);
            } else {
                console.error('Invalid response format:', data);
                alert('Received invalid response from server.');
            }
        } catch (error) {
            console.error('Error generating questions:', error);
            alert("Error generating questions.");
        } finally {
            stopFakeProgress();
            setLoading(false);
        }
    };

    const formatResponse = (response: any, index: number) => {
        if (!response) return null;

        const { lot, lots, solution, questionText, metaDetails } = response;
        const actualQuestionText = questionText || metaDetails?.questionText || "No question text found";

        return (
            <div className="formatted-response" key={index}>
                <h4>Question {index + 1}:</h4>
                <p>{actualQuestionText}</p>

                {(questionType === "SOL" || questionType === "SML") && lot?.lotItems && (
                    <>
                        <h4>Options:</h4>
                        <ul>
                            {lot.lotItems.map((item: any, idx: number) => (
                                <li key={idx}>
                                    {String.fromCharCode(65 + idx)}. {item.lotItemText}
                                </li>
                            ))}
                        </ul>
                    </>
                )}

                {questionType === "MTL" && lots && lots.length > 0 && (
                    <>
                        <h4>Matching Pairs:</h4>
                        {lots.map((lot: any, idx: number) => (
                            <div key={idx}>
                                <strong>Group {idx + 1}:</strong>
                                <ul>
                                    {lot.lotItems.map((item: any, itemIdx: number) => (
                                        <li key={itemIdx}>{item.lotItemText}</li>
                                    ))}
                                </ul>
                            </div>
                        ))}
                    </>
                )}

                {solution && (
                    <>
                        <h4>Solution:</h4>
                        {solution.SOL && lot?.lotItems && (
                            <p>
                                Correct Answer:{" "}
                                {lot.lotItems.find((item: any) => item.id === solution.SOL.itemId)?.lotItemText}
                            </p>
                        )}

                        {solution.SML && lot?.lotItems && (
                            <>
                                <p>Correct Answers:</p>
                                <ul>
                                    {lot.lotItems
                                        .filter((item: any) => solution.SML.itemIds.includes(item.id))
                                        .map((item: any, idx: number) => (
                                            <li key={idx}>{item.lotItemText}</li>
                                        ))}
                                </ul>
                            </>
                        )}

                        {solution.MTL && lots && lots.length > 0 && (
                            <>
                                <p>Correct Matching:</p>
                                <ul>
                                    {solution.MTL.matches.map((match: any, idx: number) => {
                                        const group1 = lots[0].lotItems.find(
                                            (item: any) => item.id === match.itemIds[0]
                                        )?.lotItemText;
                                        const group2 = lots[1].lotItems.find(
                                            (item: any) => item.id === match.itemIds[1]
                                        )?.lotItemText;
                                        return (
                                            <li key={idx}>
                                                {group1} ↔ {group2}
                                            </li>
                                        );
                                    })}
                                </ul>
                            </>
                        )}

                        {solution.OTL && lot?.lotItems && (
                            <>
                                <p>Correct Order:</p>
                                <ul>
                                    {solution.OTL.orders
                                        .map((order: any) =>
                                            lot.lotItems.find((item: any) => item.id === order.itemId)
                                        )
                                        .map((item: any, idx: number) => (
                                            <li key={idx}>Step {idx + 1}: {item.lotItemText}</li>
                                        ))}
                                </ul>
                            </>
                        )}
                    </>
                )}
            </div>
        );
    };

    useEffect(() => {
        return () => {
            if (progressIntervalRef.current) {
                clearInterval(progressIntervalRef.current);
            }
        };
    }, []);

    return (
        <div className="question-generator container">
            <h3>Bulk Question Generation</h3>

            <label>Question Type:</label>
            <select value={questionType} onChange={(e) => setQuestionType(e.target.value)}>
                <option value="SOL">SOL (Single Option)</option>
                <option value="SML">SML (Select Multiple)</option>
                <option value="MTL">MTL (Matching)</option>
                <option value="OTL">OTL (Ordering)</option>
            </select>

            <label>Select a Segment:</label>
            <select value={selectedSegment} onChange={(e) => setSelectedSegment(e.target.value)}>
                <option value="">Select a segment...</option>
                {segments.map((seg, idx) => (
                    <option key={idx} value={seg}>
                        {`Segment ${idx + 1}: ${seg.slice(0, 30)}...`}
                    </option>
                ))}
            </select>

            <label>Number of Questions:</label>
            <input
                type="number"
                value={numQuestions}
                min="1"
                onChange={(e) => setNumQuestions(parseInt(e.target.value))}
            />

            <button onClick={generateQuestions} disabled={loading}>
                {loading ? "Generating..." : "Generate Questions"}
            </button>

            {loading && (
                <div style={{ marginTop: "10px", width: "100%", maxWidth: "300px" }}>
                    <progress value={progress} max={100} style={{ width: "100%" }} />
                    <p>{progress}%</p>
                </div>
            )}

            {responses.length > 0 && (
                <div className="transcript-box question-response">
                    <h4>Generated Questions:</h4>
                    {responses.map((response, index) => (
                        <div key={index}>
                            {formatResponse(response, index)}
                            <hr style={{ margin: '15px 0' }} />
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default QuestionGenerator;

