const express = require("express");
const bodyParser = require("body-parser");
const { GoogleGenerativeAI } = require("@google/generative-ai");

const app = express();
const PORT = 3000;

app.use(bodyParser.json());

// Configure your Gemini API key here
const genAI = new GoogleGenerativeAI("AIzaSyDDM9X4KituIYCukvIK-b-_YN76s611hRc");

async function getGeminiModel(modelName = "gemini-pro") {
    try {
        return genAI.getGenerativeModel({ model: modelName});
    } catch (error) {
        console.warn("Warning: No API key provided or invalid key.");
        throw error;
    }
}

async function generateText(model, prompt, params) {
    try {
        const response = await model.generateContent(prompt, { ...params });
        return response.response.text();
    } catch (error) {
        return `Error: ${error.message}`;
    }
}

async function generateStructuredText(model, prompt, params, structure) {
    const structuredPrompt = `
        ${prompt}
        
        Please provide your response in the following JSON format. Ensure the response is valid JSON. Do not include any text outside of the JSON structure. Do not include any markdown code blocks.
        ${JSON.stringify(structure, null, 2)}
    `;

    try {
        const response = await model.generateContent(structuredPrompt, { ...params });
        const responseText = response.response.text();
        
        try {
            const jsonStart = responseText.indexOf("{");
            const jsonEnd = responseText.lastIndexOf("}") + 1;
            const cleanedResponse = responseText.substring(jsonStart, jsonEnd);
            return JSON.parse(cleanedResponse);
        } catch (jsonError) {
            return { error: "LLM response was not valid JSON.", rawResponse: responseText, parsingError: jsonError.message };
        }
    } catch (error) {
        return { error: `Error: ${error.message}` };
    }
}

app.post("/generate", async (req, res) => {
    const { engine = "models/gemini-1.5-pro", prompt = "", params = {} } = req.body;
    try {
        const model = await getGeminiModel(engine);
        const response = await generateText(model, prompt, params);
        res.json({ response });
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.post("/generate-structured", async (req, res) => {
    const { engine = "models/gemini-1.5-pro", prompt = "", params = {}, questionType = "MTL" } = req.body;

    const structureTypes = {
        MTL: { questionType: "MTL", questionText: "Rich Text/Markdown", hintText: "Rich Text/Markdown", timeLimit: 300, points: 20 },
        SOL: { questionType: "SOL", questionText: "Rich Text/Markdown", hintText: "Rich Text/Markdown", timeLimit: 300, points: 20 },
        SML: { questionType: "SML", questionText: "Rich Text/Markdown", hintText: "Rich Text/Markdown", timeLimit: 300, points: 20 },
        OTL: { questionType: "OTL", questionText: "Rich Text/Markdown", hintText: "Rich Text/Markdown", timeLimit: 300, points: 20 }
    };

    const structure = structureTypes[questionType] || structureTypes["MTL"];
    
    try {
        const model = await getGeminiModel(engine);
        const response = await generateStructuredText(model, prompt, params, structure);
        res.json(response);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});
