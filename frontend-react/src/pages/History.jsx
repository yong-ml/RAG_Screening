import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchHistory } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/Card';
import { Loader2, Calendar, FileText, CheckCircle, XCircle, Clock } from 'lucide-react';

export default function HistoryPage() {
    const navigate = useNavigate();
    const [history, setHistory] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadHistory();
    }, []);

    const loadHistory = async () => {
        try {
            const data = await fetchHistory();
            setHistory(data);
        } catch (error) {
            console.error('Failed to load history:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleRowClick = (sessionId) => {
        navigate('/candidates', { state: { sessionId } });
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString();
    };

    const getStatusIcon = (status) => {
        switch (status) {
            case 'COMPLETED':
                return <CheckCircle className="text-green-500" size={18} />;
            case 'FAILED':
                return <XCircle className="text-red-500" size={18} />;
            case 'PROCESSING':
                return <Loader2 className="text-blue-500 animate-spin" size={18} />;
            default:
                return <Clock className="text-slate-400" size={18} />;
        }
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-slate-400" size={48} />
            </div>
        );
    }

    return (
        <div className="max-w-5xl mx-auto space-y-6">
            <header>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Screening History</h1>
                <p className="text-slate-500 dark:text-slate-400 mt-2">View past screening sessions and results.</p>
            </header>

            <Card>
                <CardContent className="p-0">
                    {history.length === 0 ? (
                        <div className="p-8 text-center text-slate-500 dark:text-slate-400">
                            No history found. Start a new screening session.
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-left text-sm">
                                <thead className="bg-slate-50 dark:bg-slate-800/50 border-b border-slate-200 dark:border-slate-700">
                                    <tr>
                                        <th className="px-6 py-4 font-medium text-slate-700 dark:text-slate-300">ID</th>
                                        <th className="px-6 py-4 font-medium text-slate-700 dark:text-slate-300">Date</th>
                                        <th className="px-6 py-4 font-medium text-slate-700 dark:text-slate-300">Job Description</th>
                                        <th className="px-6 py-4 font-medium text-slate-700 dark:text-slate-300">Candidates</th>
                                        <th className="px-6 py-4 font-medium text-slate-700 dark:text-slate-300">Status</th>
                                        <th className="px-6 py-4 font-medium text-slate-700 dark:text-slate-300">Time</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100 dark:divide-slate-700">
                                    {history.map((session) => (
                                        <tr
                                            key={session.id}
                                            onClick={() => handleRowClick(session.id)}
                                            className="hover:bg-slate-50 dark:hover:bg-slate-800/50 cursor-pointer transition-colors"
                                        >
                                            <td className="px-6 py-4 text-slate-500 dark:text-slate-400">#{session.id}</td>
                                            <td className="px-6 py-4 text-slate-900 dark:text-slate-200 font-medium">
                                                <div className="flex items-center gap-2">
                                                    <Calendar size={14} className="text-slate-400" />
                                                    {formatDate(session.created_at)}
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-slate-600 dark:text-slate-400 max-w-xs truncate">
                                                {session.job_description_preview || "No description"}
                                            </td>
                                            <td className="px-6 py-4 text-slate-600 dark:text-slate-400">
                                                {session.total_processed}
                                            </td>
                                            <td className="px-6 py-4">
                                                <div className="flex items-center gap-2">
                                                    {getStatusIcon(session.status)}
                                                    <span className={`
                                                        ${session.status === 'COMPLETED' ? 'text-green-600 dark:text-green-400' : ''}
                                                        ${session.status === 'FAILED' ? 'text-red-600 dark:text-red-400' : ''}
                                                        ${session.status === 'PROCESSING' ? 'text-blue-600 dark:text-blue-400' : ''}
                                                    `}>
                                                        {session.status}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-4 text-slate-500 dark:text-slate-400">
                                                {session.processing_time.toFixed(1)}s
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>
        </div>
    );
}
