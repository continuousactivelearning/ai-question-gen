import { useEffect, useState } from "react";
import { fetchFiles } from "../api/api";

interface FileListProps {
    setSelectedFile: (file: string) => void;
}

const FileList: React.FC<FileListProps> = ({ setSelectedFile }) => {
    const [files, setFiles] = useState<string[]>([]);

    useEffect(() => {
        fetchFiles().then(setFiles);
    }, []);

    return (
        <div className="container">
            <h2>Uploaded Files</h2>
            <select onChange={(e) => setSelectedFile(e.target.value)}>
                <option value="">Select a file...</option>
                {files.map((file, index) => (
                    <option key={index} value={file}>{file}</option>
                ))}
            </select>
        </div>
    );
};

export default FileList;
