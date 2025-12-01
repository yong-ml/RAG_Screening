import React, { useEffect, useState } from 'react';
import { fetchServerState, fetchDbStatus, clearDb } from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '../components/Card';
import { Button } from '../components/Button';
import { FileText, Users, Database, Trash2, AlertTriangle, CheckCircle } from 'lucide-react';

export default function Dashboard() {
    const [serverState, setServerState] = useState(null);
    const [dbStatus, setDbStatus] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadData = async () => {
        try {
            const [stateData, dbData] = await Promise.all([
                fetchServerState(),
                fetchDbStatus()
            ]);
            setServerState(stateData);
            setDbStatus(dbData);
        } catch (error) {
            console.error('Failed to load dashboard data:', error);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadData();
    }, []);

    const handleClearDb = async () => {
        if (window.confirm('Are you sure you want to delete all data? This cannot be undone.')) {
            try {
                await clearDb();
                await loadData();
                alert('Database cleared successfully');
            } catch (error) {
                alert('Failed to clear database');
            }
        }
    };

    if (loading) {
        return <div className="flex items-center justify-center h-96">Loading...</div>;
    }

    return (
        <div className="space-y-6">
            <header>
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Dashboard</h1>
                <p className="text-slate-500 dark:text-slate-400 mt-2">Overview of your recruitment pipeline.</p>
            </header>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <Card>
                    <CardContent className="flex items-center gap-4">
                        <div className="p-3 bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg">
                            <FileText size={24} />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Job Description</p>
                            <p className="text-2xl font-bold text-slate-900 dark:text-white">
                                {serverState?.has_job_description ? 'Active' : 'Missing'}
                            </p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="flex items-center gap-4">
                        <div className="p-3 bg-green-100 dark:bg-green-900/30 text-green-600 dark:text-green-400 rounded-lg">
                            <Users size={24} />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Resumes Processed</p>
                            <p className="text-2xl font-bold text-slate-900 dark:text-white">
                                {serverState?.resume_count || 0}
                            </p>
                        </div>
                    </CardContent>
                </Card>

                <Card>
                    <CardContent className="flex items-center gap-4">
                        <div className="p-3 bg-purple-100 dark:bg-purple-900/30 text-purple-600 dark:text-purple-400 rounded-lg">
                            <Database size={24} />
                        </div>
                        <div>
                            <p className="text-sm font-medium text-slate-500 dark:text-slate-400">Total in DB</p>
                            <p className="text-2xl font-bold text-slate-900 dark:text-white">
                                {dbStatus?.total_count || 0}
                            </p>
                        </div>
                    </CardContent>
                </Card>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card className="h-full">
                    <CardHeader>
                        <CardTitle>System Status</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                {serverState?.has_job_description ? (
                                    <CheckCircle className="text-green-500" size={20} />
                                ) : (
                                    <AlertTriangle className="text-amber-500" size={20} />
                                )}
                                <span className="font-medium text-slate-900 dark:text-slate-200">Job Description</span>
                            </div>
                            <span className="text-sm text-slate-500 dark:text-slate-400">
                                {serverState?.has_job_description ? 'Uploaded' : 'Not Uploaded'}
                            </span>
                        </div>

                        <div className="flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-700/50 rounded-lg">
                            <div className="flex items-center gap-3">
                                {dbStatus?.has_duplicates ? (
                                    <AlertTriangle className="text-amber-500" size={20} />
                                ) : (
                                    <CheckCircle className="text-green-500" size={20} />
                                )}
                                <span className="font-medium text-slate-900 dark:text-slate-200">Database Integrity</span>
                            </div>
                            <span className="text-sm text-slate-500 dark:text-slate-400">
                                {dbStatus?.has_duplicates ? 'Duplicates Found' : 'Healthy'}
                            </span>
                        </div>
                    </CardContent>
                </Card>

                <Card className="h-full border-red-100 dark:border-red-900/30">
                    <CardHeader className="bg-red-50/50 dark:bg-red-900/10 border-red-100 dark:border-red-900/30">
                        <CardTitle className="text-red-900 dark:text-red-400">Danger Zone</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <p className="text-sm text-slate-600 dark:text-slate-400">
                            Clearing the database will remove all stored resumes and job descriptions. This action cannot be undone.
                        </p>
                        <Button variant="danger" onClick={handleClearDb} className="w-full sm:w-auto gap-2">
                            <Trash2 size={16} />
                            Clear Database
                        </Button>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
