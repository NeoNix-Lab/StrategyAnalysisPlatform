import React, { useState, useEffect } from 'react';
import { Plus, Play, Box, Activity, Calendar } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const MlDashboard = () => {
    const navigate = useNavigate();
    const [sessions, setSessions] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('http://localhost:8000/api/ml/studio/sessions')
            .then(res => res.json())
            .then(data => {
                setSessions(data);
                setLoading(false);
            })
            .catch(err => {
                console.error(err);
                setLoading(false);
            });
    }, []);

    return (
        <div className="p-8 text-slate-200">
            <header className="flex justify-between items-center mb-8">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-3">
                        <Box className="text-purple-500" />
                        ML Studio
                    </h1>
                    <p className="text-slate-400 mt-2">Manage your Reinforcement Learning experiments and training sessions.</p>
                </div>
                <button
                    onClick={() => navigate('/ml/studio/compose')}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium transition-colors shadow-lg shadow-blue-500/20"
                >
                    <Plus size={18} /> New Session
                </button>
            </header>

            {loading ? (
                <div className="text-slate-500 text-center py-20">Loading sessions...</div>
            ) : sessions.length === 0 ? (
                <div className="bg-slate-800/50 border border-slate-700 rounded-xl p-12 text-center">
                    <Box size={48} className="text-slate-600 mx-auto mb-4" />
                    <h3 className="text-xl font-semibold text-slate-300">No Training Sessions</h3>
                    <p className="text-slate-500 mt-2 mb-6">Create your first ML training session to get started.</p>
                    <button
                        onClick={() => navigate('/ml/studio/compose')}
                        className="text-blue-400 hover:text-blue-300 font-medium"
                    >
                        Create New Session &rarr;
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {sessions.map(session => (
                        <div
                            key={session.session_id}
                            onClick={() => navigate(`/ml/studio/session/${session.session_id}`)}
                            className="bg-slate-800 border border-slate-700 rounded-xl p-6 hover:bg-slate-750 hover:border-slate-600 transition-all cursor-pointer group"
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className="p-3 bg-purple-500/10 rounded-lg text-purple-400 group-hover:bg-purple-500/20 transition-colors">
                                    <Activity size={24} />
                                </div>
                                <span className={`text-xs px-2 py-1 rounded-full border ${session.status === 'ACTIVE' ? 'bg-green-500/10 border-green-500/20 text-green-400' :
                                        session.status === 'ARCHIVED' ? 'bg-slate-700 text-slate-400 border-slate-600' :
                                            'bg-blue-500/10 border-blue-500/20 text-blue-400'
                                    }`}>
                                    {session.status}
                                </span>
                            </div>

                            <h3 className="text-lg font-semibold text-slate-200 mb-2 truncate">{session.name}</h3>

                            <div className="flex items-center gap-2 text-sm text-slate-500 mb-4">
                                <Calendar size={14} />
                                <span>{new Date(session.created_utc).toLocaleDateString()}</span>
                            </div>

                            <div className="pt-4 border-t border-slate-700 flex justify-between items-center text-sm">
                                <span className="text-slate-400">Iterations</span>
                                <span className="font-mono text-slate-200 bg-slate-900 px-2 py-0.5 rounded">
                                    {/* Placeholder if we don't fetch counts in list, but api returns it? No, implemented simple list. */}
                                    View Details
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default MlDashboard;
