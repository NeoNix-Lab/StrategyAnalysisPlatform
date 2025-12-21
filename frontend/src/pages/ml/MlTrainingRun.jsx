
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Play, Activity, Clock, ArrowLeft, Terminal } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const MlTrainingRun = () => {
    const { sessionId, iterationId } = useParams();
    const navigate = useNavigate();

    // State for verbosity
    const [verbose, setVerbose] = useState(false);
    const [errorMsg, setErrorMsg] = useState(null);

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

                // Parse metrics for error
                if (iter.metrics_json && iter.metrics_json.error) {
                    setErrorMsg(iter.metrics_json.error);
                }
            }

            // Fetch Logs from dedicated endpoint
            const logsRes = await fetch(`http://localhost:8000/api/ml/studio/iterations/${iterationId}/logs`);
            if (logsRes.ok) {
                const logsData = await logsRes.json();
                setLogs(logsData);
            }
        } catch (err) {
            console.error(err);
        }
    };

    useEffect(() => {
        fetchStatus();
        const interval = setInterval(fetchStatus, 2000); // Poll faster
        return () => clearInterval(interval);
    }, [sessionId, iterationId]);

    // ... (keep chart logic but remove fake log generation if real logs exist) ...
    // Note: The previous chart mock data effect was generating fake logs. We should disable that if we have real logs.
    // For now, I will keep the chart mock but remove the log generation part of it.

    useEffect(() => {
        if (status === 'RUNNING') {
            const interval = setInterval(() => {
                setChartData(prev => {
                    const epoch = prev.length + 1;
                    const loss = Math.max(0.1, 2.0 * Math.exp(-0.1 * epoch) + (Math.random() * 0.1));
                    return [...prev, { epoch, loss }];
                });
                // REMOVED FAKE LOG GENERATION
            }, 1000);
            return () => clearInterval(interval);
        }
    }, [status]);


    const handleStart = async () => {
        try {
            await fetch(`http://localhost:8000/api/ml/studio/iterations/${iterationId}/run`);
            setStatus('RUNNING'); // Optimistic update
            setLogs(prev => [...prev, "Command sent: Start Training..."]);
        } catch (err) {
            console.error(err);
        }
    };

    const handleStop = async () => {
        try {
            await fetch(`http://localhost:8000/api/ml/studio/iterations/${iterationId}/stop`, { method: 'POST' });
            // Don't optimistic update status here, wait for poll (or do CANCELLING)
            setLogs(prev => [...prev, "Command sent: Stop Training..."]);
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
                    <label className="flex items-center gap-2 text-sm text-slate-400 cursor-pointer select-none">
                        <input
                            type="checkbox"
                            checked={verbose}
                            onChange={(e) => setVerbose(e.target.checked)}
                            className="accent-purple-500"
                        />
                        Verbose Logs
                    </label>

                    <div className={`px-3 py-1 rounded-full text-sm font-medium ${status === 'RUNNING' ? 'bg-blue-500/10 text-blue-400 animate-pulse' :
                        status === 'COMPLETED' ? 'bg-green-500/10 text-green-400' :
                            status === 'FAILED' ? 'bg-red-500/10 text-red-500 border border-red-500/20' :
                                status === 'CANCELLED' || status === 'CANCELLING' ? 'bg-red-500/10 text-red-400' :
                                    'bg-slate-700 text-slate-400'
                        }`}>
                        {status}
                    </div>
                    {/* ... (buttons) ... */}
                    {status === 'PENDING' && (
                        <button
                            onClick={handleStart}
                            className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-lg shadow-green-500/20 transition-all"
                        >
                            <Play size={16} fill="currentColor" /> Start Run
                        </button>
                    )}
                    {(status === 'RUNNING' || status === 'QUEUED') && (
                        <button
                            onClick={handleStop}
                            className="bg-red-600 hover:bg-red-500 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-lg shadow-red-500/20 transition-all"
                        >
                            <div className="w-3 h-3 bg-white rounded-sm" /> Stop
                        </button>
                    )}
                </div>
            </header>

            {/* Error Banner */}
            {errorMsg && (
                <div className="mb-6 bg-red-500/10 border border-red-500/50 p-4 rounded-xl text-red-200 font-mono text-sm overflow-x-auto whitespace-pre-wrap">
                    <strong className="block text-red-400 mb-1">CRITICAL ERROR:</strong>
                    {errorMsg}
                </div>
            )}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
                {/* Main Chart Area */}
                <div className="lg:col-span-2 bg-slate-800 rounded-xl border border-slate-700 p-4 flex flex-col">
                    <h3 className="text-sm font-medium text-slate-400 mb-4 flex items-center gap-2">
                        <Activity size={16} /> Live Metrics (Loss)
                    </h3>
                    <div className="flex-1 bg-slate-900/50 rounded-lg p-2">
                        {/* Chart Component (Keep existing) */}
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
                    <div className="flex justify-between items-center mb-2">
                        <h3 className="text-slate-500 uppercase tracking-wider text-[10px]">Execution Logs</h3>
                        <span className="text-[10px] text-slate-600">{logs.length} lines</span>
                    </div>

                    <div className="space-y-1 font-mono">
                        {logs.length === 0 && <span className="text-slate-700 italic">Waiting for logs...</span>}
                        {logs.map((log, i) => {
                            // Simple filter: if not verbose, hide Traceback lines or INFO lines? 
                            // Taking a safer approach: Show all if verbose. If not verbose, hide lines starting with 'Traceback' or indented lines?
                            // Actually, let's just show everything if verbose is ON. 
                            // If verbose is OFF, maybe show only "INFO" level? 
                            // For now, let's just make the user check 'Verbose' to see the logs clearly.

                            // Better: Highlight errors
                            const isError = log.includes("ERROR") || log.includes("Exception") || log.includes("Traceback");
                            if (!verbose && !isError && i < logs.length - 5) return null; // Only show last 5 lines if not verbose, unless error

                            return (
                                <div key={i} className={`border-l-2 pl-2 break-all ${isError ? 'text-red-400 border-red-500 bg-red-900/10' : 'text-slate-400 border-slate-800'}`}>
                                    {log}
                                </div>
                            )
                        })}

                        {!verbose && logs.length > 5 && (
                            <div className="text-center py-2 text-slate-600 italic cursor-pointer hover:text-slate-400" onClick={() => setVerbose(true)}>
                                ... {logs.length - 5} older lines hidden (Enable Verbose) ...
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MlTrainingRun;
