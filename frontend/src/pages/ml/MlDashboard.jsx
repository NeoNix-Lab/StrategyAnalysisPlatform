
import React, { useState, useEffect } from 'react';
import {
    Play, BarChart2, CheckCircle, AlertTriangle, Plus,
    ArrowRight, Activity, Brain, Zap, Database, Clock, MoreHorizontal
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import {
    AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import '../Dashboard.css'; // Reuse Analyst Dashboard styles for uniformity

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
            const response = await fetch('/api/ml/studio/sessions');
            if (response.ok) {
                const data = await response.json();
                setSessions(data);
                calculateStats(data);
            }
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

    return (
        <div className="dashboard-container">
            {/* Header with Action Button */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <h1 style={{ margin: 0, fontSize: '1.8rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                    Quant Laboratory
                </h1>
                <button
                    onClick={() => navigate('/ml/studio/compose')}
                    style={{
                        background: 'linear-gradient(135deg, #7c3aed, #a855f7)',
                        color: 'white',
                        border: 'none',
                        padding: '0.6rem 1.25rem',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        fontWeight: 600,
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.5rem',
                        boxShadow: '0 4px 6px -1px rgba(124, 58, 237, 0.3)'
                    }}
                >
                    <Plus size={18} /> New Experiment
                </button>
            </div>

            {/* Main Stats Grid (Identical structure to Dashboard.jsx) */}
            <div className="dashboard-grid">
                <div className="card">
                    <div className="card-icon"><Database size={24} color="#a78bfa" /></div>
                    <h3>Total Experiments</h3>
                    <div className="metric-value">{stats.total}</div>
                </div>
                <div className="card">
                    <div className="card-icon"><Activity size={24} color="#d8b4fe" /></div>
                    <h3>Active Runs</h3>
                    <div className="metric-value" style={{ color: stats.active > 0 ? '#d8b4fe' : 'inherit' }}>
                        {stats.active}
                    </div>
                </div>
                <div className="card">
                    <div className="card-icon"><CheckCircle size={24} color="#4ade80" /></div>
                    <h3>Success Rate</h3>
                    <div className="metric-value" style={{ color: '#4ade80' }}>
                        {stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0}%
                    </div>
                </div>
                <div className="card">
                    <div className="card-icon"><Zap size={24} color="#fbbf24" /></div>
                    <h3>Compute Load</h3>
                    <div className="metric-value" style={{ color: '#fbbf24' }}>34%</div>
                </div>
                <div className="card">
                    <div className="card-icon"><AlertTriangle size={24} color="#f87171" /></div>
                    <h3>Failed</h3>
                    <div className="metric-value" style={{ color: '#f87171' }}>{stats.failed}</div>
                </div>
            </div>

            {/* Charts Section */}
            <div className="charts-grid" style={{ marginTop: '2rem' }}>
                <div className="card chart-card" style={{ gridColumn: '1 / -1' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                        <h3>Weekly Activity</h3>
                        <div style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Last 7 Days</div>
                    </div>
                    <div className="chart-container" style={{ height: '300px' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={activityData}>
                                <defs>
                                    <linearGradient id="colorRuns" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#a855f7" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#a855f7" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
                                <XAxis dataKey="name" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff', borderRadius: '8px' }}
                                />
                                <Area type="monotone" dataKey="runs" stroke="#a855f7" strokeWidth={2} fillOpacity={1} fill="url(#colorRuns)" />
                            </AreaChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Recent Training Sessions Table (Consistent Table Style) */}
            <div className="card" style={{ marginTop: '2rem' }}>
                <div className="card-header" style={{ marginBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ margin: 0 }}>Recent Experiments</h3>
                    <button
                        style={{
                            background: 'transparent',
                            border: 'none',
                            color: '#a855f7',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            fontSize: '0.9rem',
                            padding: '0.5rem'
                        }}
                    >
                        View All <ArrowRight size={16} />
                    </button>
                </div>
                <div className="table-container" style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                        <thead>
                            <tr style={{ borderBottom: '1px solid #334155', textAlign: 'left', color: '#94a3b8' }}>
                                <th style={{ padding: '1rem' }}>Experiment Name</th>
                                <th style={{ padding: '1rem' }}>Status</th>
                                <th style={{ padding: '1rem' }}>Model</th>
                                <th style={{ padding: '1rem' }}>Dataset</th>
                                <th style={{ padding: '1rem', textAlign: 'right' }}>Created</th>
                                <th style={{ padding: '1rem', textAlign: 'right' }}>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {loading ? (
                                <tr><td colSpan="6" style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>Loading...</td></tr>
                            ) : sessions.length === 0 ? (
                                <tr><td colSpan="6" style={{ padding: '2rem', textAlign: 'center', color: '#64748b' }}>No experiments found</td></tr>
                            ) : (
                                sessions.map((session) => (
                                    <tr
                                        key={session.session_id}
                                        onClick={() => navigate(`/ ml / studio / session / ${session.session_id} `)}
                                        style={{ borderBottom: '1px solid #1e293b', cursor: 'pointer', transition: 'background 0.2s' }}
                                        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(30, 41, 59, 0.5)'}
                                        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                                    >
                                        <td style={{ padding: '1rem', fontWeight: 500, color: '#f1f5f9' }}>
                                            {session.name}
                                            <div style={{ fontSize: '0.75rem', color: '#64748b', fontFamily: 'monospace' }}>
                                                {session.session_id.substring(0, 8)}
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem' }}>
                                            <StatusBadge status={session.status} />
                                        </td>
                                        <td style={{ padding: '1rem', color: '#cbd5e1' }}>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <Brain size={14} color="#a78bfa" />
                                                {session.algorithm || 'Unknown'}
                                            </div>
                                        </td>
                                        <td style={{ padding: '1rem', color: '#cbd5e1' }}>
                                            {session.dataset_name || 'N/A'}
                                        </td>
                                        <td style={{ padding: '1rem', textAlign: 'right', color: '#94a3b8' }}>
                                            {new Date(session.created_at).toLocaleDateString()}
                                        </td>
                                        <td style={{ padding: '1rem', textAlign: 'right' }}>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); navigate(`/ml/studio/session/${session.session_id}`); }}
                                                style={{ padding: '0.5rem', background: 'rgba(147, 51, 234, 0.15)', color: '#d8b4fe', border: 'none', borderRadius: '4px', cursor: 'pointer', marginRight: '0.5rem' }}
                                                title="Run/Console"
                                            >
                                                <Play size={14} />
                                            </button>
                                            <button
                                                onClick={(e) => e.stopPropagation()}
                                                style={{ padding: '0.5rem', background: 'transparent', color: '#94a3b8', border: 'none', cursor: 'pointer' }}
                                            >
                                                <MoreHorizontal size={16} />
                                            </button>
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

// Start Helper Component
const StatusBadge = ({ status }) => {
    let color = '#94a3b8';
    let bg = 'rgba(148, 163, 184, 0.1)';
    const s = status?.toLowerCase();

    if (s === 'running') { color = '#a855f7'; bg = 'rgba(168, 85, 247, 0.15)'; }
    else if (s === 'completed') { color = '#4ade80'; bg = 'rgba(74, 222, 128, 0.15)'; }
    else if (s === 'failed') { color = '#f87171'; bg = 'rgba(248, 113, 113, 0.15)'; }

    return (
        <span style={{
            color, background: bg,
            padding: '0.25rem 0.75rem',
            borderRadius: '99px',
            fontSize: '0.75rem',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em'
        }}>
            {status}
        </span>
    );
};

export default MlDashboard;
