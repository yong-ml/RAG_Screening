import React, { useEffect, useRef, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Button } from '../components/Button';
import { ChevronLeft, FileText, Brain, BookOpen, GripVertical, ChevronRight } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { renderAsync } from 'docx-preview';
import { getResumeUrl } from '../services/api';
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels';
import { clsx } from 'clsx';

export default function CandidateDetailPage() {
    const location = useLocation();
    const navigate = useNavigate();
    const { candidate, jobDescription } = location.state || {};
    const docxContainerRef = useRef(null);
    const [loadingResume, setLoadingResume] = useState(false);
    const [isJdCollapsed, setIsJdCollapsed] = useState(false);

    useEffect(() => {
        if (!candidate) {
            navigate('/candidates');
            return;
        }
    }, [candidate, navigate]);

    useEffect(() => {
        const renderDocx = async () => {
            if (candidate && docxContainerRef.current && candidate.filename?.toLowerCase().endsWith('.docx')) {
                setLoadingResume(true);
                try {
                    docxContainerRef.current.innerHTML = '';
                    const response = await fetch(getResumeUrl(candidate.filename));
                    const blob = await response.blob();
                    await renderAsync(blob, docxContainerRef.current);
                } catch (error) {
                    console.error('Failed to render DOCX:', error);
                    docxContainerRef.current.innerHTML = '<p class="text-red-500 p-4">Failed to load document preview.</p>';
                } finally {
                    setLoadingResume(false);
                }
            }
        };

        renderDocx();
    }, [candidate]);

    if (!candidate) return null;

    const ResizeHandle = ({ className = "" }) => (
        <PanelResizeHandle className={clsx("w-4 bg-transparent hover:bg-blue-50/50 transition-colors flex items-center justify-center group outline-none z-10", className)}>
            <div className="w-1 h-8 rounded-full bg-slate-200 dark:bg-slate-700 group-hover:bg-blue-400 transition-colors" />
        </PanelResizeHandle>
    );

    return (
        <div className="h-screen flex flex-col bg-slate-50 dark:bg-slate-900/50 p-4 overflow-hidden">
            <header className="flex items-center justify-between shrink-0 mb-4 px-2">
                <div className="flex items-center gap-4">
                    <Button
                        variant="ghost"
                        onClick={() => navigate(-1)}
                        className="gap-2 hover:bg-white dark:hover:bg-slate-800"
                    >
                        <ChevronLeft size={20} />
                        Back to Candidates
                    </Button>
                    <div>
                        <h1 className="text-2xl font-bold text-slate-900 dark:text-white">{candidate.name}</h1>
                        <p className="text-slate-500 dark:text-slate-400 text-sm">Gemini Score: {candidate.gemini_score}/100</p>
                    </div>
                </div>
            </header>

            <div className="flex-1 min-h-0">
                <PanelGroup direction="horizontal" autoSaveId="candidate-detail-layout">
                    {/* Column 1: Job Description */}
                    <Panel
                        defaultSize={20}
                        minSize={15}
                        collapsible={true}
                        onCollapse={() => setIsJdCollapsed(true)}
                        onExpand={() => setIsJdCollapsed(false)}
                        className={clsx("flex flex-col", isJdCollapsed && "min-w-[50px]")}
                    >
                        <div className="h-full flex flex-col bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                            <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50 shrink-0 flex items-center justify-between h-[52px]">
                                {!isJdCollapsed ? (
                                    <>
                                        <h3 className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2 truncate">
                                            <BookOpen size={18} className="text-green-500 shrink-0" />
                                            <span className="truncate">Job Description</span>
                                        </h3>
                                    </>
                                ) : (
                                    <div className="w-full flex justify-center">
                                        <BookOpen size={20} className="text-green-500" />
                                    </div>
                                )}
                            </div>
                            {!isJdCollapsed && (
                                <div className="flex-1 overflow-y-auto p-6">
                                    <div className="prose prose-sm max-w-none text-slate-700 dark:text-slate-300 dark:prose-invert">
                                        <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                            {jobDescription || 'No job description available.'}
                                        </ReactMarkdown>
                                    </div>
                                </div>
                            )}
                        </div>
                    </Panel>

                    <ResizeHandle />

                    {/* Column 2: AI Report */}
                    <Panel defaultSize={40} minSize={20}>
                        <div className="h-full flex flex-col bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                            <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50 shrink-0 h-[52px] flex items-center">
                                <h3 className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                                    <Brain size={18} className="text-purple-500" />
                                    AI Analysis Report
                                </h3>
                            </div>
                            <div className="flex-1 overflow-y-auto p-6">
                                <div className="prose prose-sm max-w-none text-slate-700 dark:text-slate-300 dark:prose-invert">
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {candidate.gemini_analysis}
                                    </ReactMarkdown>
                                </div>
                                {candidate.thinking_process && (
                                    <div className="mt-6 pt-6 border-t border-slate-200 dark:border-slate-700">
                                        <h4 className="text-xs font-semibold text-slate-500 uppercase mb-2">Reasoning Process</h4>
                                        <div className="text-xs font-mono bg-slate-50 dark:bg-slate-900 text-slate-600 dark:text-slate-400 p-3 rounded border border-slate-200 dark:border-slate-700 whitespace-pre-wrap">
                                            {candidate.thinking_process}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </Panel>

                    <ResizeHandle />

                    {/* Column 3: Resume Viewer */}
                    <Panel defaultSize={40} minSize={20}>
                        <div className="h-full flex flex-col bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
                            <div className="p-3 border-b border-slate-200 dark:border-slate-700 bg-slate-50/50 dark:bg-slate-900/50 shrink-0 h-[52px] flex items-center">
                                <h3 className="font-semibold text-slate-700 dark:text-slate-300 flex items-center gap-2">
                                    <FileText size={18} className="text-blue-500" />
                                    Resume Preview
                                </h3>
                            </div>
                            <div className="flex-1 overflow-y-auto bg-slate-100 dark:bg-slate-900 relative">
                                {candidate.filename?.toLowerCase().endsWith('.docx') ? (
                                    <div
                                        ref={docxContainerRef}
                                        className="w-full min-h-full bg-white p-8 shadow-sm"
                                    />
                                ) : (
                                    <iframe
                                        src={getResumeUrl(candidate.filename)}
                                        className="w-full h-full bg-white"
                                        title="Resume Preview"
                                    />
                                )}
                                {loadingResume && (
                                    <div className="absolute inset-0 flex items-center justify-center bg-white/80 dark:bg-slate-900/80 z-10">
                                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
                                    </div>
                                )}
                            </div>
                        </div>
                    </Panel>
                </PanelGroup>
            </div>
        </div>
    );
}
