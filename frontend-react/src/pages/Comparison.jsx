import React, { useEffect, useState } from 'react';
import { fetchServerState, compareCandidates } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/Card';
import { Button } from '../components/Button';
import { GitCompare, ArrowRight, Loader2, Brain } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

export default function ComparisonPage() {
    const [candidates, setCandidates] = useState([]);
    const [selected1, setSelected1] = useState('');
    const [selected2, setSelected2] = useState('');
    const [comparison, setComparison] = useState(null);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const loadCandidates = async () => {
            try {
                const state = await fetchServerState();
                if (state.screening_result?.candidates) {
                    setCandidates(state.screening_result.candidates);
                    if (state.screening_result.candidates.length >= 2) {
                        setSelected1(state.screening_result.candidates[0].name);
                        setSelected2(state.screening_result.candidates[1].name);
                    }
                }
            } catch (error) {
                console.error('Failed to load candidates:', error);
            }
        };
        loadCandidates();
    }, []);

    const handleCompare = async () => {
        if (!selected1 || !selected2 || selected1 === selected2) {
            alert('Please select two different candidates.');
            return;
        }

        setLoading(true);
        try {
            const result = await compareCandidates(selected1, selected2);
            setComparison(result);
        } catch (error) {
            console.error('Comparison failed:', error);
            alert('Failed to compare candidates.');
        } finally {
            setLoading(false);
        }
    };

    if (candidates.length < 2) {
        return (
            <div className="text-center py-20">
                <h2 className="text-2xl font-bold text-slate-700">Not enough candidates</h2>
                <p className="text-slate-500 mt-2">You need at least 2 candidates to perform a comparison.</p>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <header>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Compare Candidates</h1>
                <p className="text-slate-500 dark:text-slate-400 mt-2">Side-by-side analysis of two candidates.</p>
            </header>

            <Card>
                <CardContent className="p-6">
                    <div className="flex flex-col md:flex-row items-center gap-6">
                        <div className="flex-1 w-full">
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Candidate A</label>
                            <select
                                className="w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-colors"
                                value={selected1}
                                onChange={(e) => setSelected1(e.target.value)}
                            >
                                {candidates
                                    .filter((c) => c.name !== selected2)
                                    .map((c) => (
                                        <option key={c.name} value={c.name}>{c.name}</option>
                                    ))
                                }
                            </select>
                        </div>

                        <div className="flex items-center justify-center bg-slate-100 dark:bg-slate-700 rounded-full p-2 text-slate-500 dark:text-slate-400">
                            <GitCompare size={24} />
                        </div>

                        <div className="flex-1 w-full">
                            <label className="block text-sm font-medium text-slate-700 dark:text-slate-300 mb-2">Candidate B</label>
                            <select
                                className="w-full h-10 rounded-lg border border-slate-300 dark:border-slate-700 bg-white dark:bg-slate-800 text-slate-900 dark:text-white px-3 py-2 focus:ring-2 focus:ring-blue-500 focus:outline-none transition-colors"
                                value={selected2}
                                onChange={(e) => setSelected2(e.target.value)}
                            >
                                {candidates
                                    .filter((c) => c.name !== selected1)
                                    .map((c) => (
                                        <option key={c.name} value={c.name}>{c.name}</option>
                                    ))
                                }
                            </select>
                        </div>

                        <Button
                            onClick={handleCompare}
                            disabled={loading || selected1 === selected2}
                            className="w-full md:w-auto mt-6 md:mt-0"
                        >
                            {loading ? <Loader2 className="animate-spin" /> : 'Compare'}
                        </Button>
                    </div>
                </CardContent>
            </Card>

            {comparison && (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
                    {/* Candidate 1 Stats */}
                    <Card className="border-blue-100 dark:border-blue-900/30 bg-blue-50/30 dark:bg-blue-900/10">
                        <CardHeader>
                            <CardTitle className="text-blue-900 dark:text-blue-400">{comparison.candidate1_name}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-1 gap-4">
                                <div className="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-slate-100 dark:border-slate-700">
                                    <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">Gemini Score</p>
                                    <p className="text-2xl font-bold text-slate-900 dark:text-white">{comparison.candidate1_gemini_score}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Candidate 2 Stats */}
                    <Card className="border-purple-100 dark:border-purple-900/30 bg-purple-50/30 dark:bg-purple-900/10">
                        <CardHeader>
                            <CardTitle className="text-purple-900 dark:text-purple-400">{comparison.candidate2_name}</CardTitle>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="grid grid-cols-1 gap-4">
                                <div className="bg-white dark:bg-slate-800 p-4 rounded-lg shadow-sm border border-slate-100 dark:border-slate-700">
                                    <p className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase">Gemini Score</p>
                                    <p className="text-2xl font-bold text-slate-900 dark:text-white">{comparison.candidate2_gemini_score}</p>
                                </div>
                            </div>
                        </CardContent>
                    </Card>

                    {/* Comparison Text */}
                    <Card className="lg:col-span-2 border-slate-200 dark:border-slate-700 shadow-md">
                        <CardHeader className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-100 dark:border-slate-700">
                            <CardTitle className="flex items-center gap-2">
                                <Brain className="text-indigo-500" />
                                <span className="text-slate-900 dark:text-white">AI Comparative Analysis</span>
                            </CardTitle>
                        </CardHeader>
                        <CardContent className="p-8">
                            <div className="prose prose-lg max-w-none text-slate-700 dark:text-slate-300 leading-relaxed dark:prose-invert">
                                {comparison?.comparison ? (
                                    <ReactMarkdown remarkPlugins={[remarkGfm]}>
                                        {comparison.comparison}
                                    </ReactMarkdown>
                                ) : (
                                    <p>No comparison data available.</p>
                                )}
                            </div>
                        </CardContent>
                    </Card>
                </div>
            )}
        </div>
    );
}
