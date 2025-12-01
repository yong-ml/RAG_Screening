import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { LayoutDashboard, Upload, Users, GitCompare, Database, Moon, Sun, ChevronLeft, ChevronRight } from 'lucide-react';
import { clsx } from 'clsx';
import { useTheme } from '../context/ThemeContext';

const navItems = [
    { icon: LayoutDashboard, label: 'Dashboard', path: '/' },
    { icon: Upload, label: 'Upload', path: '/upload' },
    { icon: Users, label: 'Candidates', path: '/candidates' },
    { icon: GitCompare, label: 'Compare', path: '/compare' },
    { icon: Database, label: 'History', path: '/history' },
];

export function Layout({ children }) {
    const location = useLocation();
    const { theme, toggleTheme } = useTheme();
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-900 flex transition-colors duration-300">
            {/* Sidebar */}
            <aside className={clsx(
                "bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 fixed h-full z-10 transition-all duration-300",
                isSidebarCollapsed ? "w-16" : "w-64"
            )}>
                {/* Toggle Button */}
                <button
                    onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                    className="absolute -right-3 top-6 w-6 h-6 bg-white dark:bg-slate-700 border border-slate-200 dark:border-slate-600 rounded-full flex items-center justify-center text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-600 shadow-md transition-colors z-20"
                >
                    {isSidebarCollapsed ? <ChevronRight size={14} /> : <ChevronLeft size={14} />}
                </button>

                <div className="p-6 border-b border-slate-100 dark:border-slate-700">
                    <h1 className={clsx(
                        "text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2 transition-all duration-300",
                        isSidebarCollapsed && "justify-center"
                    )}>
                        <span className="text-2xl">🚀</span>
                        {!isSidebarCollapsed && "AI Recruiter"}
                    </h1>
                </div>

                <nav className="p-4 space-y-1">
                    {navItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = location.pathname === item.path;

                        return (
                            <Link
                                key={item.path}
                                to={item.path}
                                className={clsx(
                                    'flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors',
                                    isActive
                                        ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400'
                                        : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 hover:text-slate-900 dark:hover:text-slate-200',
                                    isSidebarCollapsed && 'justify-center px-2'
                                )}
                                title={isSidebarCollapsed ? item.label : ''}
                            >
                                <Icon size={20} />
                                {!isSidebarCollapsed && item.label}
                            </Link>
                        );
                    })}
                </nav>

                <div className="absolute bottom-0 w-full p-4 border-t border-slate-100 dark:border-slate-700 space-y-4">
                    <button
                        onClick={toggleTheme}
                        className={clsx(
                            "flex items-center gap-3 px-4 py-2 w-full rounded-lg text-sm font-medium text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors",
                            isSidebarCollapsed && "justify-center px-2"
                        )}
                        title={isSidebarCollapsed ? (theme === 'light' ? 'Dark Mode' : 'Light Mode') : ''}
                    >
                        {theme === 'light' ? <Moon size={20} /> : <Sun size={20} />}
                        {!isSidebarCollapsed && (theme === 'light' ? 'Dark Mode' : 'Light Mode')}
                    </button>

                    {!isSidebarCollapsed && (
                        <div className="flex items-center gap-3 px-4 py-3 text-sm text-slate-500 dark:text-slate-400">
                            <div className="w-2 h-2 rounded-full bg-green-500"></div>
                            System Online
                        </div>
                    )}
                </div>
            </aside>

            {/* Main Content */}
            <main className={clsx(
                "flex-1 transition-all duration-300",
                isSidebarCollapsed ? "ml-16" : "ml-64",
                location.pathname.startsWith('/candidates/view') ? "p-0" : "p-8"
            )}>
                <div className={clsx(
                    location.pathname.startsWith('/candidates/view') ? "h-full" : "max-w-7xl mx-auto"
                )}>
                    {children}
                </div>
            </main>
        </div>
    );
}
