
import React, { useState, useEffect } from 'react';
import {
    Play, BarChart2, CheckCircle, AlertTriangle, Plus,
    ArrowRight, Activity, Brain, Zap, Database, Clock, MoreHorizontal
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';

import api from '../../api/axios';

const MlDashboard = () => {
    const navigate = useNavigate();
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [stats, setStats] = useState({
        total: 0,
        active: 0,
        completed: 0,
        failed: 0
    });

    // Mock data for weekly activity
    const activityData = [
        { name: 'Mon', runs: 4 },
        { name: 'Tue', runs: 7 },
        { name: 'Wed', runs: 5 },
        { name: 'Thu', runs: 12 },
        { name: 'Fri', runs: 8 },
        { name: 'Sat', runs: 3 },
        { name: 'Sun', runs: 6 },
    ];

    useEffect(() => {
        fetchSessions();
    }, []);

    const fetchSessions = async () => {
        try {
            const response = await api.get('/ml/studio/sessions');
            const data = response.data;
            setSessions(data);
            calculateStats(data);
        } catch (error) {
            console.error("Failed to fetch sessions:", error);
        } finally {
            setLoading(false);
        }
    };

    const calculateStats = (data) => {
        const newStats = data.reduce((acc, session) => {
            acc.total++;
            if (session.status === 'running') acc.active++;
            else if (session.status === 'completed') acc.completed++;
            else if (session.status === 'failed' || session.status === 'error') acc.failed++;
            return acc;
        }, { total: 0, active: 0, completed: 0, failed: 0 });
        setStats(newStats);
    };

    const cardClass = "bg-bg-secondary/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-xl hover:border-violet-500/30 transition-all";
    const kpiLabelClass = "text-sm text-text-secondary uppercase tracking-wider font-semibold mb-2";
    const kpiValueClass = "text-3xl font-bold text-text-primary";

    return (
        <div className="max-w-[1600px] mx-auto space-y-8 animate-fade-in">
            {/* Header with Action Button */}
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-fuchsia-400">
                        Quant Laboratory
                    </h1>
                    <p className="text-text-secondary text-sm mt-1">Machine Learning Experimentation Studio</p>
                </div>

                <button
                    onClick={() => navigate('/ml/studio/compose')}
                    className="flex items-center gap-2 px-5 py-2.5 bg-violet-600 hover:bg-violet-500 text-white rounded-xl shadow-lg shadow-violet-900/40 transition-all font-semibold"
                >
                    <Plus size={18} /> New Experiment
                </button>
            </div>

            {/* Main Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
                <div className={cardClass}>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-violet-500/10 rounded-lg"><Database size={20} className="text-violet-400" /></div>
                        <h3 className={kpiLabelClass}>Total Experiments</h3>
                    </div>
                    <div className={kpiValueClass}>{stats.total}</div>
                </div>

                <div className={cardClass}>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-fuchsia-500/10 rounded-lg"><Activity size={20} className="text-fuchsia-400" /></div>
                        <h3 className={kpiLabelClass}>Active Runs</h3>
                    </div>
                    <div className={`${kpiValueClass} ${stats.active > 0 ? 'text-fuchsia-400' : ''}`}>
                        {stats.active}
                    </div>
                </div>

                <div className={cardClass}>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-green-500/10 rounded-lg"><CheckCircle size={20} className="text-green-400" /></div>
                        <h3 className={kpiLabelClass}>Success Rate</h3>
                    </div>
                    <div className={`${kpiValueClass} text-green-400`}>
                        {stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0}%
                    </div>
                </div>

                <div className={cardClass}>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-amber-500/10 rounded-lg"><Zap size={20} className="text-amber-400" /></div>
                        <h3 className={kpiLabelClass}>Compute Load</h3>
                    </div>
                    <div className={`${kpiValueClass} text-amber-400`}>34%</div>
                </div>

                <div className={cardClass}>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-rose-500/10 rounded-lg"><AlertTriangle size={20} className="text-rose-400" /></div>
                        <h3 className={kpiLabelClass}>Failed</h3>
                    </div>
                    <div className={`${kpiValueClass} text-rose-400`}>{stats.failed}</div>
                </div>
            </div>

            {/* Charts Section */}
            <div className="grid grid-cols-1">
                <div className={`${cardClass} h-[400px] flex flex-col`}>
                    <div className="flex justify-between mb-4">
                        <h3 className="font-bold text-lg text-text-primary">Weekly Activity</h3>
                        <span className="text-xs text-text-secondary uppercase tracking-wider font-semibold">Last 7 Days</span>
                    </div>
                    <div className="flex-1 w-full min-h-0">
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={activityData}>
                                <defs>
                                    <linearGradient id="colorRuns" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                                <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff', borderRadius: '8px' }}
                                />
                                <Area type="monotone" dataKey="runs" stroke="#8b5cf6" strokeWidth={3} fillOpacity={1} fill="url(#colorRuns)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Recent Training Sessions Table */}
            <div className={`${cardClass} p-0 overflow-hidden`}>
                <div className="p-6 border-b border-slate-700/50 flex justify-between items-center bg-bg-secondary/30">
                    <h3 className="text-lg font-bold text-text-primary m-0">Recent Experiments</h3>
                    <button className="text-violet-400 hover:text-violet-300 text-sm font-medium flex items-center gap-1 transition-colors">
                        View All <ArrowRight size={16} />
                    </button>
                </div>
                <div className="overflow-x-auto custom-scrollbar">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-slate-900/50 text-xs uppercase font-semibold text-text-secondary">
                            <tr>
                                <th className="p-4 border-b border-slate-700/50">Experiment Name</th>
                                <th className="p-4 border-b border-slate-700/50">Status</th>
                                <th className="p-4 border-b border-slate-700/50">Model</th>
                                <th className="p-4 border-b border-slate-700/50">Dataset</th>
                                <th className="p-4 border-b border-slate-700/50 text-right">Created</th>
                                <th className="p-4 border-b border-slate-700/50 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {loading ? (
                                <tr><td colSpan="6" className="p-8 text-center text-text-secondary">Loading...</td></tr>
                            ) : sessions.length === 0 ? (
                                <tr><td colSpan="6" className="p-8 text-center text-text-secondary">No experiments found</td></tr>
                            ) : (
                                sessions.map((session) => (
                                    <tr
                                        key={session.session_id}
                                        onClick={() => navigate(`/ml/studio/session/${session.session_id}`)}
                                        className="hover:bg-violet-500/5 transition-colors cursor-pointer group"
                                    >
                                        <td className="p-4 text-slate-100 font-medium">
                                            {session.name}
                                            <div className="text-[10px] text-text-muted font-mono mt-0.5 group-hover:text-violet-400 transition-colors">
                                                {session.session_id.substring(0, 8)}
                                            </div>
                                        </td>
                                        <td className="p-4">
                                            <StatusBadge status={session.status} />
                                        </td>
                                        <td className="p-4 text-slate-300">
                                            <div className="flex items-center gap-2">
                                                <Brain size={14} className="text-violet-400" />
                                                {session.algorithm || 'Unknown'}
                                            </div>
                                        </td>
                                        <td className="p-4 text-slate-300">
                                            {session.dataset_name || 'N/A'}
                                        </td>
                                        <td className="p-4 text-right text-text-secondary">
                                            {new Date(session.created_at).toLocaleDateString()}
                                        </td>
                                        <td className="p-4 text-right">
                                            <div className="flex justify-end gap-2">
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); navigate(`/ml/studio/session/${session.session_id}`); }}
                                                    className="p-1.5 bg-violet-500/10 text-violet-400 hover:bg-violet-500/20 rounded transition-colors"
                                                    title="Run/Console"
                                                >
                                                    <Play size={14} />
                                                </button>
                                                <button
                                                    onClick={(e) => e.stopPropagation()}
                                                    className="p-1.5 text-text-secondary hover:text-text-primary hover:bg-white/5 rounded transition-colors"
                                                >
                                                    <MoreHorizontal size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
};

// Helper Component
const StatusBadge = ({ status }) => {
    const s = status?.toLowerCase();

    let colorClass = "bg-slate-500/10 text-slate-400";
    if (s === 'running') colorClass = "bg-violet-500/15 text-violet-400 animate-pulse";
    if (s === 'completed') colorClass = "bg-green-500/15 text-green-400";
    if (s === 'failed') colorClass = "bg-rose-500/15 text-rose-400";

    return (
        <span className={`px-3 py-1 rounded-full text-[10px] uppercase font-bold tracking-wider ${colorClass}`}>
            {status}
        </span>
    );
};

export default MlDashboard;
