const API_URL = import.meta.env.VITE_API_URL;


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


export const generateStructuredQuestion = async (questionType: string, segment: string) => {
    try {
        const response = await fetch(`${API_URL}/generate-structured`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                questionType,
                prompt: `Generate a ${questionType} question based on the following segment: "${segment}"`,
                params: {
                    temperature: 0.7
                }
            })
        });
    
        if (!response.ok) {
            throw new Error('Failed to generate question');
        }
    
        const data = await response.json();
        return data;
    } catch (error) {
        console.error("Error generating structured question:", error);
        return { error: "Failed to generate question" };
    }
};
