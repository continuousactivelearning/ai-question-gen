import { useState } from "react";
import { generateStructuredQuestion } from "../api/api";

interface QuestionGeneratorProps {
    segments: string[];
}

const QuestionGenerator: React.FC<QuestionGeneratorProps> = ({ segments }) => {
    const [questionType, setQuestionType] = useState("MTL");
    const [selectedSegment, setSelectedSegment] = useState<string>("");
    const [numQuestions, setNumQuestions] = useState<number>(1);
    const [responses, setResponses] = useState<any[]>([]);

    const [loading, setLoading] = useState<boolean>(false);

const generateQuestions = async () => {
    if (!selectedSegment || numQuestions < 1) {
        alert("Please select a valid segment and number of questions.");
        return;
    }

    setLoading(true);
    setResponses([]);
    const batchSize = 3;
    const allResponses: any[] = [];

    try {
        for (let i = 0; i < numQuestions; i += batchSize) {
            const batch = Array.from({ length: Math.min(batchSize, numQuestions - i) }, () =>
                generateStructuredQuestion(questionType, selectedSegment)
            );

            const batchResponses = await Promise.all(batch);
            allResponses.push(...batchResponses);
            setResponses([...allResponses]);
        }
    } catch (error) {
        console.error("Error generating questions:", error);
        alert("Error generating questions.");
    } finally {
        setLoading(false);
    }
};

    

    const formatResponse = (response: any, index: number) => {
        if (!response) return null;

        const { questionText, lot, lots, solution } = response;

        return (
            <div className="formatted-response" key={index}>
                <h4>Question {index + 1}:</h4>
                <p>{questionText}</p>

                {/* Display Options for SOL and SML */}
                {lot?.lotItems && (
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

                {/* Display Matching Options for MTL */}
                {lots && lots.length > 0 && (
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

                {/* Solution Formatting */}
                <h4>Solution:</h4>
                {solution.SOL && (
                    <p>
                        Correct Answer:{" "}
                        {lot.lotItems.find((item: any) => item.id === solution.SOL.itemId)?.lotItemText}
                    </p>
                )}

                {solution.SML && (
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

                {solution.MTL && (
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

                {solution.OTL && (
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
            </div>
        );
    };

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

            <button onClick={generateQuestions} disabled={loading}>{loading ? "Generating..." : "Generate Questions"}</button>


            {responses.length > 0 && (
                <div className="transcript-box question-response">
                    <h4>Generated Questions:</h4>
                    {responses.map((response, index) => formatResponse(response, index))}
                </div>
            )}
        </div>
    );
};

export default QuestionGenerator;
