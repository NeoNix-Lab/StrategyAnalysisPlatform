
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Play, Activity, Clock, ArrowLeft, Terminal } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const MlTrainingRun = () => {
    const { sessionId, iterationId } = useParams();
    const navigate = useNavigate();

    const [iteration, setIteration] = useState(null);
    const [status, setStatus] = useState('LOADING');
    const [logs, setLogs] = useState([]);
    const [chartData, setChartData] = useState([]);

    const fetchStatus = async () => {
        try {
            const res = await fetch(`http://localhost:8000/api/ml/studio/sessions/${sessionId}`);
            const data = await res.json();
            const iter = data.iterations.find(i => i.iteration_id === iterationId);
            if (iter) {
                setIteration(iter);
                setStatus(iter.status);
            }
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 5000);
        return () => clearInterval(interval);
    }, [sessionId, iterationId]);

    // Mock Chart Data for Running State
    useEffect(() => {
        if (status === 'RUNNING') {
            const interval = setInterval(() => {
                setChartData(prev => {
                    const epoch = prev.length + 1;
                    const loss = Math.max(0.1, 2.0 * Math.exp(-0.1 * epoch) + (Math.random() * 0.1));
                    return [...prev, { epoch, loss }];
                });
                setLogs(prev => [...prev, `[${new Date().toLocaleTimeString()}] Epoch ${prev.length + 1} completed. Loss: 0.xyz`]);
            }, 1000);
            return () => clearInterval(interval);
        }
    }, [status]);

    const handleStart = async () => {
        try {
            await fetch(`http://localhost:8000/api/ml/studio/iterations/${iterationId}/run`);
            setStatus('RUNNING');
            setLogs(prev => [...prev, "Command sent: Start Training..."]);
        } catch (err) {
            console.error(err);
        }
    };

    if (!iteration && status === 'LOADING') return <div className="p-8 text-slate-400">Loading...</div>;

    return (
        <div className="p-6 h-[calc(100vh-64px)] flex flex-col text-slate-200">
            <button
                onClick={() => navigate(`/ml/studio/session/${sessionId}`)}
                className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-4 transition-colors w-fit"
            >
                <ArrowLeft size={16} /> Back to Session
            </button>

            <header className="flex justify-between items-center mb-6 bg-slate-800 p-4 rounded-xl border border-slate-700">
                <div>
                    <h1 className="text-xl font-bold flex items-center gap-2">
                        <Terminal className="text-purple-500" />
                        Training Console
                        <span className="text-slate-500 font-normal text-sm ml-2">({iterationId?.slice(0, 8)})</span>
                    </h1>
                </div>
                <div className="flex items-center gap-4">
                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${status === 'RUNNING' ? 'bg-blue-500/10 text-blue-400 animate-pulse' :
                            status === 'COMPLETED' ? 'bg-green-500/10 text-green-400' :
                                'bg-slate-700 text-slate-400'
                        }`}>
                        {status}
                    </div>
                    {status === 'PENDING' && (
                        <button
                            onClick={handleStart}
                            className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-lg shadow-green-500/20 transition-all"
                        >
                            <Play size={16} fill="currentColor" /> Start Run
                        </button>
                    )}
                </div>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
                {/* Main Chart Area */}
                <div className="lg:col-span-2 bg-slate-800 rounded-xl border border-slate-700 p-4 flex flex-col">
                    <h3 className="text-sm font-medium text-slate-400 mb-4 flex items-center gap-2">
                        <Activity size={16} /> Live Metrics (Loss)
                    </h3>
                    <div className="flex-1 bg-slate-900/50 rounded-lg p-2">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="epoch" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }}
                                    itemStyle={{ color: '#e2e8f0' }}
                                />
                                <Line type="monotone" dataKey="loss" stroke="#8b5cf6" strokeWidth={2} dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Sidebar Logs */}
                <div className="bg-slate-950 rounded-xl border border-slate-800 p-4 font-mono text-xs overflow-y-auto flex flex-col">
                    <h3 className="text-slate-500 mb-2 uppercase tracking-wider text-[10px]">Execution Logs</h3>
                    <div className="space-y-1">
                        {logs.length === 0 && <span className="text-slate-700 italic">Waiting for logs...</span>}
                        {logs.map((log, i) => (
                            <div key={i} className="text-slate-400 border-l-2 border-slate-800 pl-2">
                                <span className="text-slate-600 mr-2">{log.split(']')[0]}]</span>
                                {log.split(']')[1]}
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MlTrainingRun;
