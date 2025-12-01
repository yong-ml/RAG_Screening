import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { screenResumes } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/Card';
import { Button } from '../components/Button';
import { Input, Textarea } from '../components/Input';
import { Upload as UploadIcon, FileText, X, Loader2 } from 'lucide-react';

export default function UploadPage() {
    const navigate = useNavigate();
    const [jdMethod, setJdMethod] = useState('text'); // 'text' | 'file' | 'none'
    const [jdText, setJdText] = useState('');
    const [jdFile, setJdFile] = useState(null);
    const [resumes, setResumes] = useState([]);
    const [topN, setTopN] = useState(10);
    const [loading, setLoading] = useState(false);

    const [progress, setProgress] = useState(0);
    const [statusMessage, setStatusMessage] = useState('');

    const handleFileChange = (e, type) => {
        if (type === 'jd') {
            if (e.target.files?.[0]) {
                setJdFile(e.target.files[0]);
            }
        } else {
            if (e.target.files) {
                setResumes(Array.from(e.target.files));
            }
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setProgress(0);
        setStatusMessage('Initializing...');

        try {
            const formData = new FormData();

            // Add JD
            if (jdMethod === 'text' && jdText) {
                formData.append('job_description', jdText);
            } else if (jdMethod === 'file' && jdFile) {
                formData.append('job_description_file', jdFile);
            }

            // Add Resumes
            resumes.forEach((file) => {
                formData.append('resumes', file);
            });

            // Add Config
            formData.append('top_n', topN);

            // Start Screening
            const initResult = await screenResumes(formData);
            const sessionId = initResult.session_id;
            setStatusMessage('Screening started...');

            // Poll for status
            const pollInterval = setInterval(async () => {
                try {
                    const status = await import('../services/api').then(m => m.fetchScreeningStatus(sessionId));

                    if (status.status === 'PROCESSING') {
                        const percent = status.total_processed > 0
                            ? Math.round((status.processed_count / status.total_processed) * 100)
                            : 0;
                        setProgress(percent);
                        setStatusMessage(`Analyzing candidates... ${status.processed_count}/${status.total_processed}`);
                    } else if (status.status === 'COMPLETED') {
                        clearInterval(pollInterval);
                        navigate('/candidates', { state: { results: status.result } });
                    } else if (status.status === 'FAILED') {
                        clearInterval(pollInterval);
                        alert('Screening failed.');
                        setLoading(false);
                    }
                } catch (err) {
                    console.error("Polling error", err);
                    // Don't stop polling immediately on one error, but maybe limit retries
                }
            }, 2000);

        } catch (error) {
            console.error('Upload failed:', error);
            alert('Analysis failed. Please try again.');
            setLoading(false);
        }
    };

    return (
        <div className="max-w-3xl mx-auto space-y-6">
            <header>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Upload Data</h1>
                <p className="text-slate-500 dark:text-slate-400 mt-2">Upload job description and resumes for analysis.</p>
            </header>

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Job Description Section */}
                <Card>
                    <CardHeader>
                        <CardTitle>Job Description</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex gap-4 p-1 bg-slate-100 dark:bg-slate-900 rounded-lg w-fit">
                            <button
                                type="button"
                                onClick={() => setJdMethod('text')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${jdMethod === 'text' ? 'bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                Text Input
                            </button>
                            <button
                                type="button"
                                onClick={() => setJdMethod('file')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${jdMethod === 'file' ? 'bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                File Upload
                            </button>
                            <button
                                type="button"
                                onClick={() => setJdMethod('none')}
                                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${jdMethod === 'none' ? 'bg-white dark:bg-slate-700 shadow-sm text-slate-900 dark:text-white' : 'text-slate-500 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200'
                                    }`}
                            >
                                Use Existing
                            </button>
                        </div>

                        {jdMethod === 'text' && (
                            <Textarea
                                placeholder="Paste the job description here..."
                                value={jdText}
                                onChange={(e) => setJdText(e.target.value)}
                                className="h-48"
                            />
                        )}

                        {jdMethod === 'file' && (
                            <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-lg p-8 text-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                                <input
                                    type="file"
                                    id="jd-file"
                                    className="hidden"
                                    onChange={(e) => handleFileChange(e, 'jd')}
                                    accept=".txt,.pdf,.docx"
                                />
                                <label htmlFor="jd-file" className="cursor-pointer flex flex-col items-center gap-2">
                                    <UploadIcon className="text-slate-400" size={32} />
                                    <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                                        {jdFile ? jdFile.name : 'Click to upload JD file'}
                                    </span>
                                    <span className="text-xs text-slate-500 dark:text-slate-400">PDF, DOCX, TXT</span>
                                </label>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Resumes Section */}
                <Card>
                    <CardHeader>
                        <CardTitle>Resumes</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-lg p-8 text-center hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors">
                            <input
                                type="file"
                                id="resume-files"
                                className="hidden"
                                multiple
                                onChange={(e) => handleFileChange(e, 'resumes')}
                                accept=".pdf,.docx"
                            />
                            <label htmlFor="resume-files" className="cursor-pointer flex flex-col items-center gap-2">
                                <FileText className="text-slate-400" size={32} />
                                <span className="text-sm font-medium text-slate-700 dark:text-slate-300">
                                    {resumes.length > 0
                                        ? `${resumes.length} files selected`
                                        : 'Click to upload resumes'}
                                </span>
                                <span className="text-xs text-slate-500 dark:text-slate-400">PDF, DOCX (Multiple allowed)</span>
                            </label>
                        </div>

                        {resumes.length > 0 && (
                            <div className="bg-slate-50 dark:bg-slate-900/50 rounded-lg p-4 max-h-40 overflow-y-auto space-y-2">
                                {resumes.map((file, index) => (
                                    <div key={index} className="flex items-center justify-between text-sm">
                                        <span className="truncate text-slate-700 dark:text-slate-300">{file.name}</span>
                                        <button
                                            type="button"
                                            onClick={() => setResumes(resumes.filter((_, i) => i !== index))}
                                            className="text-slate-400 hover:text-red-500 transition-colors"
                                        >
                                            <X size={14} />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </CardContent>
                </Card>

                {/* Settings */}
                <Card>
                    <CardContent className="flex items-center justify-between py-4">
                        <span className="font-medium text-slate-700 dark:text-slate-300">Top Candidates to Analyze</span>
                        <div className="flex items-center gap-4">
                            <span className="text-sm text-slate-500 dark:text-slate-400">{topN} candidates</span>
                            <input
                                type="range"
                                min="5"
                                max="50"
                                value={topN}
                                onChange={(e) => setTopN(parseInt(e.target.value))}
                                className="w-32"
                            />
                        </div>
                    </CardContent>
                </Card>

                <Button
                    type="submit"
                    className="w-full h-12 text-lg gap-2"
                    disabled={loading || (jdMethod !== 'none' && !jdText && !jdFile) || (resumes.length === 0 && jdMethod !== 'none')}
                >
                    {loading ? (
                        <div className="flex flex-col items-center w-full">
                            <div className="flex items-center gap-2">
                                <Loader2 className="animate-spin" />
                                <span>{statusMessage}</span>
                            </div>
                            <div className="w-full bg-slate-700 rounded-full h-2 mt-2">
                                <div
                                    className="bg-blue-400 h-2 rounded-full transition-all duration-500"
                                    style={{ width: `${progress}%` }}
                                />
                            </div>
                        </div>
                    ) : (
                        'Start Analysis'
                    )}
                </Button>
            </form>
        </div>
    );
}
