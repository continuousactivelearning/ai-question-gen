/*import { useState, useEffect } from "react";
import AudioRecorder from "./components/AudioRecorder";
import FileList from "./components/FileList";
import TranscriptGenerator from "./components/TranscriptGenerator";
import QuestionGenerator from "./components/QuestionGenerator";
import { fetchFiles } from "./api/api";

const App: React.FC = () => {
    const [files, setFiles] = useState<string[]>([]);
    const [selectedFile, setSelectedFile] = useState<string>("");

    const refreshFiles = async () => {
        const fileList = await fetchFiles();
        setFiles(fileList);
    };

    useEffect(() => {
        refreshFiles();
    }, []);

    return (
        <div>
            <AudioRecorder refreshFiles={refreshFiles} />
            <FileList setSelectedFile={setSelectedFile} />
            <TranscriptGenerator selectedFile={selectedFile} />
            <QuestionGenerator />
        </div>
    );
};

export default App;*/

import { useState, useEffect } from "react";
import AudioRecorder from "./components/AudioRecorder";
import FileList from "./components/FileList";
import TranscriptGenerator from "./components/TranscriptGenerator";
import { fetchFiles } from "./api/api";

const App: React.FC = () => {
    const [files, setFiles] = useState<string[]>([]);
    const [selectedFile, setSelectedFile] = useState<string>("");

    const refreshFiles = async () => {
        const fileList = await fetchFiles();
        setFiles(fileList);
    };

    useEffect(() => {
        refreshFiles();
    }, []);

    return (
        <div>
            <AudioRecorder refreshFiles={refreshFiles} />
            <FileList setSelectedFile={setSelectedFile} />
            <TranscriptGenerator selectedFile={selectedFile} />
        </div>
    );
};

export default App;
