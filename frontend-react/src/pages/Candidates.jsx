import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { fetchServerState, fetchScreeningStatus, exportSession } from '../services/api';
import { Card } from '../components/Card';
import { Button } from '../components/Button';
import { ChevronDown, ChevronUp, Award, Brain, Download, Search, SlidersHorizontal } from 'lucide-react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function CandidatesPage() {
    const location = useLocation();
    const navigate = useNavigate();
    const [candidates, setCandidates] = useState([]);
    const [expandedId, setExpandedId] = useState(null);
    const [loading, setLoading] = useState(true);
    const [sessionId, setSessionId] = useState(null);
    const [minScore, setMinScore] = useState(0);
    const [searchKeyword, setSearchKeyword] = useState('');
    const [jobDescription, setJobDescription] = useState('');

    useEffect(() => {
        const loadResults = async () => {
            setLoading(true);
            try {
                if (location.state?.results) {
                    setCandidates(location.state.results.top_candidates);
                    setJobDescription(location.state.results.job_description || '');
                    if (location.state.results.session_id) {
                        setSessionId(location.state.results.session_id);
                    }
                } else if (location.state?.sessionId) {
                    setSessionId(location.state.sessionId);
                    const status = await fetchScreeningStatus(location.state.sessionId);
                    if (status.result?.top_candidates) {
                        setCandidates(status.result.top_candidates);
                    }
                    if (status.result?.job_description) {
                        setJobDescription(status.result.job_description);
                    }
                } else {
                    const state = await fetchServerState();
                    if (state.screening_result?.candidates) {
                        setCandidates(state.screening_result.candidates);
                    }
                    if (state.screening_result?.job_description) {
                        setJobDescription(state.screening_result.job_description);
                    }
                }
            } catch (error) {
                console.error('Failed to load candidates:', error);
            } finally {
                setLoading(false);
            }
        };

        loadResults();
    }, [location.state]);

    const handleExport = async () => {
        if (!sessionId) {
            alert('Session ID not found. Cannot export.');
            return;
        }
        try {
            const blob = await exportSession(sessionId);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `screening_results_${sessionId}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error) {
            console.error('Export failed:', error);
            alert('Failed to export results.');
        }
    };

    const filteredCandidates = candidates.filter(candidate => {
        const matchesScore = candidate.gemini_score >= minScore;
        const matchesKeyword = searchKeyword === '' ||
            candidate.name.toLowerCase().includes(searchKeyword.toLowerCase()) ||
            (candidate.gemini_analysis && candidate.gemini_analysis.toLowerCase().includes(searchKeyword.toLowerCase()));
        return matchesScore && matchesKeyword;
    });

    // Always sort by Gemini score descending
    const sortedCandidates = [...filteredCandidates].sort((a, b) => {
        return b.gemini_score - a.gemini_score;
    });

    const handleViewResume = (candidate) => {
        navigate('/candidates/view', {
            state: {
                candidate,
                jobDescription
            }
        });
    };

    if (loading) return <div className="p-8 text-center">Loading results...</div>;

    if (candidates.length === 0) {
        return (
            <div className="text-center py-20">
                <h2 className="text-2xl font-bold text-slate-700">No results found</h2>
                <p className="text-slate-500 mt-2">Upload resumes to see analysis results.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <header className="flex flex-col gap-6">
                <div className="flex items-center justify-between">
                    <div>
                        <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Candidates</h1>
                        <p className="text-slate-500 dark:text-slate-400 mt-2">Top {filteredCandidates.length} candidates found.</p>
                    </div>

                    <div className="flex gap-4">
                        {sessionId && (
                            <Button onClick={handleExport} variant="outline" className="gap-2">
                                <Download size={16} />
                                Export Excel
                            </Button>
                        )}
                    </div>
                </div>

                <Card className="bg-slate-50 dark:bg-slate-900/50 border-slate-200 dark:border-slate-700">
                    <div className="p-4 flex flex-wrap items-center gap-6">
                        <div className="flex-1 min-w-[200px]">
                            <div className="relative">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                                <input
                                    type="text"
                                    placeholder="Search candidates or keywords..."
                                    value={searchKeyword}
                                    onChange={(e) => setSearchKeyword(e.target.value)}
                                    className="w-full pl-10 pr-4 py-2 rounded-lg border border-slate-200 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                                />
                            </div>
                        </div>

                        <div className="flex items-center gap-4 min-w-[300px]">
                            <div className="flex items-center gap-2 text-slate-600 dark:text-slate-400">
                                <SlidersHorizontal size={18} />
                                <span className="text-sm font-medium whitespace-nowrap">Min Score: {minScore}</span>
                            </div>
                            <input
                                type="range"
                                min="0"
                                max="100"
                                value={minScore}
                                onChange={(e) => setMinScore(Number(e.target.value))}
                                className="w-full h-2 bg-slate-200 dark:bg-slate-700 rounded-lg appearance-none cursor-pointer accent-blue-600"
                            />
                        </div>
                    </div>
                </Card>
            </header>

            <div className="space-y-4">
                {sortedCandidates.map((candidate, index) => (
                    <motion.div
                        key={candidate.name}
                        initial={{ opacity: 0, y: 20 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.05 }}
                    >
                        <Card className={clsx(
                            'transition-all duration-200',
                            expandedId === index ? 'ring-2 ring-blue-500 shadow-lg' : 'hover:shadow-md'
                        )}>
                            <div className="p-6 flex items-center justify-between">
                                <div className="flex items-center gap-4">
                                    <div className="flex items-center justify-center w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-300 font-bold">
                                        {index + 1}
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-bold text-slate-900 dark:text-white">{candidate.name}</h3>
                                        <p className="text-sm text-slate-500 dark:text-slate-400 line-clamp-2 max-w-xl mt-1">
                                            {candidate.jina_reasoning || 'No summary available'}
                                        </p>
                                    </div>
                                </div>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleViewResume(candidate);
                                    }}
                                    className="text-blue-600 hover:text-blue-700 hover:bg-blue-50 dark:text-blue-400 dark:hover:bg-blue-900/30 gap-1"
                                >
                                    View Resume
                                </Button>
                            </div>

                            <div className="flex items-center gap-8 px-6 pb-6">
                                <div className="text-right ml-auto">
                                    <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">Gemini Score</p>
                                    <div className="flex items-center justify-end gap-1">
                                        <span className={clsx(
                                            "text-xl font-bold",
                                            candidate.gemini_score >= 80 ? "text-green-600 dark:text-green-400" :
                                                candidate.gemini_score >= 60 ? "text-amber-600 dark:text-amber-400" : "text-red-600 dark:text-red-400"
                                        )}>
                                            {candidate.gemini_score}
                                        </span>
                                        <span className="text-sm text-slate-400">/100</span>
                                    </div>
                                </div>
                                <button
                                    onClick={() => setExpandedId(expandedId === index ? null : index)}
                                    className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-200 transition-colors cursor-pointer p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"
                                    aria-label={expandedId === index ? "Collapse details" : "Expand details"}
                                >
                                    {expandedId === index ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
                                </button>
                            </div>

                            <AnimatePresence>
                                {expandedId === index && (
                                    <motion.div
                                        initial={{ height: 0, opacity: 0 }}
                                        animate={{ height: 'auto', opacity: 1 }}
                                        exit={{ height: 0, opacity: 0 }}
                                        className="overflow-hidden border-t border-slate-100 dark:border-slate-700"
                                    >
                                        <div className="p-6 bg-slate-50/50 dark:bg-slate-900/30 space-y-6">
                                            {/* Summary Section in Detail View */}
                                            <div>
                                                <h4 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white mb-3">
                                                    <Search size={18} className="text-blue-500" />
                                                    Summary
                                                </h4>
                                                <div className="text-sm text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700">
                                                    {candidate.jina_reasoning || 'No summary available'}
                                                </div>
                                            </div>

                                            <div>
                                                <h4 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white mb-3">
                                                    <Brain size={18} className="text-purple-500" />
                                                    AI Analysis
                                                </h4>
                                                <div className="prose prose-sm max-w-none text-slate-600 dark:text-slate-300 bg-white dark:bg-slate-800 p-4 rounded-lg border border-slate-200 dark:border-slate-700 dark:prose-invert">
                                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                                        {candidate.gemini_analysis}
                                                    </ReactMarkdown>
                                                </div>
                                            </div>

                                            {candidate.thinking_process && (
                                                <div>
                                                    <h4 className="flex items-center gap-2 font-semibold text-slate-900 dark:text-white mb-3">
                                                        <Award size={18} className="text-amber-500" />
                                                        Reasoning Process
                                                    </h4>
                                                    <div className="text-xs font-mono bg-slate-900 dark:bg-black text-slate-300 p-4 rounded-lg overflow-x-auto border border-slate-800 dark:border-slate-800 whitespace-pre-wrap">
                                                        {candidate.thinking_process}
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </motion.div>
                                )}
                            </AnimatePresence>
                        </Card>
                    </motion.div>
                ))}
            </div>
        </div>
    );
}
