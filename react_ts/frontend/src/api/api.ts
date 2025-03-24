const API_URL = "http://127.0.0.1:5000";

export const uploadAudio = async (audioBlob: Blob, filename: string): Promise<{ message?: string; error?: string }> => {
    const formData = new FormData();
    formData.append("audio", audioBlob, filename + ".wav");

    try {
        const response = await fetch(`${API_URL}/upload-audio`, {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Server error: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error("Upload error:", error);
        return { error: (error as Error).message };
    }
};

export const fetchFiles = async (): Promise<string[]> => {
    const response = await fetch(`${API_URL}/get-files`);
    return response.json();
};

export const generateTranscript = async (filename: string): Promise<{ transcript?: string; error?: string }> => {
    const response = await fetch(`${API_URL}/generateTranscript`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ filename: `./static/uploads/${filename}` }),
    });
    return response.json();
};

export const generateStructuredQuestion = async (questionType: string, prompt: string) => {
    const response = await fetch("http://127.0.0.1:5000/generate-structured", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ questionType, prompt, params: {} }),
    });

    return response.json();
};