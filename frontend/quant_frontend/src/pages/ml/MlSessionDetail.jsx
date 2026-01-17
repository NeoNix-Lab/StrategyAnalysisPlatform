import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Database, Clock, Plus, Zap, Layers, RefreshCw } from 'lucide-react';

const MlSessionDetail = () => {
    const { sessionId } = useParams();
    const navigate = useNavigate();
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(true);
    const [datasets, setDatasets] = useState([]);
    const [selectedIterationId, setSelectedIterationId] = useState(null);
    const [iterationLogs, setIterationLogs] = useState([]);
    const [logsLoading, setLogsLoading] = useState(false);
    const [logsError, setLogsError] = useState(null);

    // New Iteration State
    const [showNewIter, setShowNewIter] = useState(false);
    const [selectedDataset, setSelectedDataset] = useState('');
    const [splitConfig, setSplitConfig] = useState({ train: 0.7, test: 0.2, work: 0.1 });

    // Validation State
    const [validating, setValidating] = useState(false);
    const [validationResult, setValidationResult] = useState(null); // { valid: bool, error: str, result: float }
    const [rewardCode, setRewardCode] = useState(null);
    const [previewData, setPreviewData] = useState(null); // { columns: [], data: [] }

    // Fetch Reward Code when session is loaded
    useEffect(() => {
        if (session && session.function && session.function.id) {
            fetch(`http://localhost:8000/api/ml/studio/functions/${session.function.id}`)
                .then(res => res.json())
                .then(data => setRewardCode(data.code))
                .catch(err => console.error("Failed to fetch reward code", err));
        }
    }, [session]);

    // Validate when dataset is selected and we have code
    useEffect(() => {
        if (selectedDataset && rewardCode) {
            validateRewardOnDataset();
        } else {
            setValidationResult(null);
        }

        if (selectedDataset) {
            fetchDatasetPreview();
        } else {
            setPreviewData(null);
        }
    }, [selectedDataset, rewardCode]);

    const fetchDatasetPreview = async () => {
        try {
            const res = await fetch(`http://localhost:8000/api/datasets/${selectedDataset}/preview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ limit: 5, offset: 0 })
            });
            const data = await res.json();
            setPreviewData(data);
        } catch (err) {
            console.error("Preview fetch failed", err);
        }
    };

    const validateRewardOnDataset = async () => {
        setValidating(true);
        setValidationResult(null);
        try {
            const res = await fetch('http://localhost:8000/api/ml/studio/functions/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code: rewardCode,
                    dataset_id: selectedDataset,
                })
            });
            const data = await res.json();
            setValidationResult(data);
        } catch (err) {
            console.error(err);
            setValidationResult({ valid: false, error: "Validation request failed" });
        } finally {
            setValidating(false);
        }
    };

    useEffect(() => {
        Promise.all([
            fetch(`http://localhost:8000/api/ml/studio/sessions/${sessionId}`).then(res => res.json()),
            fetch('http://localhost:8000/api/datasets/').then(res => res.json())
        ]).then(([sessionData, datasetsData]) => {
            setSession(sessionData);
            setDatasets(datasetsData);
            setLoading(false);
        }).catch(err => console.error(err));
    }, [sessionId]);

    // Auto-refresh session data every 5 seconds when there are running iterations
    useEffect(() => {
        if (!session || !session.iterations) return;

        const hasRunningIterations = session.iterations.some(iter => iter.status === 'RUNNING');
        if (!hasRunningIterations) return;

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/ml/studio/sessions/${sessionId}`);
                const sessionData = await res.json();
                setSession(sessionData);
            } catch (err) {
                console.error('Failed to refresh session data:', err);
            }
        }, 5000);

        return () => clearInterval(interval);
    }, [session, sessionId]);

    const handleCreateIteration = async () => {
        if (!selectedDataset) return;
        if (validationResult && !validationResult.valid) return;

        try {
            const res = await fetch('http://localhost:8000/api/ml/studio/iterations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    dataset_id: selectedDataset,
                    split_config: splitConfig
                })
            });

            if (res.ok) {
                // Refresh session or navigate? Maybe stay and show the new iteration
                // For now, reload
                window.location.reload();
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleRerunIteration = async (iteration) => {
        if (!window.confirm(`Are you sure you want to re-run this iteration on ${iteration.dataset_name}?`)) {
            return;
        }

        try {
            const res = await fetch(`http://localhost:8000/api/ml/studio/iterations/${iteration.iteration_id}/run`, {
                method: 'POST'
            });

            if (res.ok) {
                // Refresh the session data to show updated status
                const sessionRes = await fetch(`http://localhost:8000/api/ml/studio/sessions/${sessionId}`);
                const sessionData = await sessionRes.json();
                setSession(sessionData);
            } else {
                alert('Failed to re-run iteration');
            }
        } catch (err) {
            console.error(err);
            alert('Failed to re-run iteration');
        }
    };

    const fetchIterationLogs = useCallback(async (iterationId) => {
        if (!iterationId) return;
        setLogsLoading(true);
        setLogsError(null);
        try {
            const res = await fetch(`http://localhost:8000/api/ml/studio/iterations/${iterationId}/logs?limit=500`);
            if (!res.ok) throw new Error("Failed to fetch logs");
            const data = await res.json();
            setIterationLogs(Array.isArray(data) ? data : []);
        } catch (err) {
            console.error(err);
            setLogsError("Failed to load logs");
        } finally {
            setLogsLoading(false);
        }
    }, []);

    useEffect(() => {
        if (!selectedIterationId) return;
        fetchIterationLogs(selectedIterationId);
    }, [selectedIterationId, fetchIterationLogs]);

    useEffect(() => {
        if (!session || !selectedIterationId) return;
        const selectedIteration = session.iterations?.find(iter => iter.iteration_id === selectedIterationId);
        const shouldPoll = selectedIteration && ["RUNNING", "QUEUED", "PENDING"].includes(selectedIteration.status);
        if (!shouldPoll) return;

        const interval = setInterval(() => fetchIterationLogs(selectedIterationId), 10000);
        return () => clearInterval(interval);
    }, [session, selectedIterationId, fetchIterationLogs]);

    if (loading) return <div className="p-8 text-slate-400">Loading session...</div>;
    if (!session) return <div className="p-8 text-red-400">Session not found</div>;

    return (
        <div className="p-8 text-slate-200">
            <button
                onClick={() => navigate('/ml/studio')}
                className="flex items-center gap-2 text-slate-400 hover:text-purple-400 mb-6 transition-colors"
                style={{ fontSize: '0.9rem', fontWeight: 500 }}
            >
                <ArrowLeft size={18} /> Back to Studio
            </button>

            {/* Header Card */}
            <div className="relative overflow-hidden rounded-xl border border-slate-700 mb-8 shadow-2xl"
                style={{
                    background: 'linear-gradient(145deg, #0f172a 0%, #1e293b 100%)',
                }}>
                <div className="absolute top-0 right-0 p-32 bg-purple-600/10 blur-[100px] rounded-full pointer-events-none"></div>

                <div className="relative p-8 flex justify-between items-start">
                    <div>
                        <div className="flex items-center gap-3 mb-3">
                            <div className="p-3 bg-purple-500/10 rounded-lg border border-purple-500/20">
                                <Zap className="text-purple-400" size={24} />
                            </div>
                            <div>
                                <h1 className="text-3xl font-bold text-white tracking-tight">{session.name}</h1>
                                <div className="text-xs text-purple-400 font-mono mt-1 opacity-70">ID: {session.session_id}</div>
                            </div>
                        </div>

                        <div className="flex gap-6 text-sm text-slate-400 mt-6">
                            <div className="flex items-center gap-2 px-4 py-2 bg-[#0b1121] rounded-lg border border-slate-800">
                                <Layers size={14} className="text-blue-400" />
                                <span className="text-slate-500">Model:</span>
                                <span className="text-slate-200 font-medium">{session.model?.name}</span>
                            </div>
                            <div className="flex items-center gap-2 px-4 py-2 bg-[#0b1121] rounded-lg border border-slate-800">
                                <Clock size={14} className="text-green-400" />
                                <span className="text-slate-500">Process:</span>
                                <span className="text-slate-200 font-medium">{session.process?.name}</span>
                            </div>
                        </div>
                    </div>

                    <div className="flex flex-col items-end gap-3">
                        <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider ${session.status === 'PLANNED' ? 'bg-slate-700 text-slate-300' :
                            session.status === 'ACTIVE' ? 'bg-purple-500/20 text-purple-300 border border-purple-500/30' :
                                'bg-slate-700 text-slate-300'
                            }`}>
                            {session.status}
                        </span>
                        <div className="text-xs text-slate-500">Created: {new Date(session.created_utc).toLocaleDateString()}</div>
                    </div>
                </div>
            </div>

            {/* Iterations Section */}
            <div className="mb-6 flex justify-between items-center">
                <h2 className="text-xl font-bold flex items-center gap-2">
                    <Database size={20} className="text-purple-400" />
                    Iterations History
                </h2>
                <button
                    onClick={() => setShowNewIter(!showNewIter)}
                    style={{
                        background: 'linear-gradient(135deg, #7c3aed, #a855f7)',
                        boxShadow: '0 4px 6px -1px rgba(124, 58, 237, 0.3)'
                    }}
                    className="flex items-center gap-2 text-white px-5 py-2.5 rounded-lg text-sm font-semibold hover:opacity-90 transition-opacity"
                >
                    <Plus size={18} strokeWidth={2.5} /> New Iteration
                </button>
            </div>

            {/* New Iteration Form Card */}
            {showNewIter && (
                <div className="bg-[#0f172a] border border-purple-500/30 p-6 rounded-xl mb-8 animate-in fade-in slide-in-from-top-4 shadow-xl">
                    <h3 className="font-semibold mb-6 flex items-center gap-2 text-purple-300">
                        <Play size={16} className="fill-purple-300" /> Launch Configuration
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-6">
                        <div>
                            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Target Dataset</label>
                            <select
                                className="w-full bg-[#0b1121] border border-slate-700 rounded-lg p-3 text-sm text-slate-200 focus:border-purple-500 focus:ring-1 focus:ring-purple-500 outline-none transition-all"
                                value={selectedDataset}
                                onChange={(e) => setSelectedDataset(e.target.value)}
                            >
                                <option value="" disabled>Select a dataset to train on...</option>
                                {datasets.map(d => (
                                    <option key={d.dataset_id} value={d.dataset_id}>{d.name} ({d.symbol} {d.timeframe})</option>
                                ))}
                            </select>

                            <div className="mt-2 p-2 bg-blue-500/10 border border-blue-500/20 rounded-lg text-[10px] text-blue-300 flex items-start gap-2">
                                <div className="mt-0.5">ℹ️</div>
                                <div>
                                    <strong className="block mb-0.5">Input Feature Policy</strong>
                                    Non-numeric columns (e.g. timestamps) are automatically excluded from the model input. Future updates will allow custom encoding strategies.
                                </div>
                            </div>

                            {/* Validation Status */}
                            {selectedDataset && (
                                <div className="mt-3">
                                    {validating && <div className="text-xs text-purple-400 flex items-center gap-2 animate-pulse"><Clock size={12} /> Validating Reward Function...</div>}
                                    {!validating && validationResult && (
                                        <div className={`p-3 rounded-lg border text-xs ${validationResult.valid
                                            ? 'bg-green-500/10 border-green-500/30 text-green-300'
                                            : 'bg-red-500/10 border-red-500/30 text-red-300'
                                            }`}>
                                            {validationResult.valid ? (
                                                <div className="flex items-center gap-2">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-green-400"></div>
                                                    <span>Compatible (Dry Run: {validationResult.result?.toFixed(4)})</span>
                                                </div>
                                            ) : (
                                                <div className="flex flex-col gap-1">
                                                    <div className="flex items-center gap-2 font-bold">
                                                        <div className="w-1.5 h-1.5 rounded-full bg-red-400"></div>
                                                        <span>Incompatible Dataset</span>
                                                    </div>
                                                    <span className="opacity-80 font-mono">{validationResult.error}</span>
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>
                            )}

                            {/* Dataset Preview */}
                            {previewData && previewData.data && previewData.data.length > 0 && (
                                <div className="mt-4">
                                    <div className="text-[10px] uppercase tracking-wider text-slate-500 font-bold mb-2 flex justify-between">
                                        <span>Data Preview (Last 5 rows)</span>
                                        <span className="text-purple-400 cursor-pointer hover:underline" onClick={() => setPreviewData(null)}>Hide</span>
                                    </div>
                                    <div className="overflow-x-auto rounded-lg border border-slate-700 bg-[#0f172a]">
                                        <table className="w-full text-xs text-left text-slate-400">
                                            <thead className="bg-slate-800 text-slate-300 font-mono">
                                                <tr>
                                                    {previewData.columns.map(col => (
                                                        <th key={col} className="px-3 py-2 border-b border-slate-700 font-medium">{col}</th>
                                                    ))}
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-800 font-mono">
                                                {previewData.data.slice(0, 5).map((row, i) => (
                                                    <tr key={i} className="hover:bg-slate-800/30">
                                                        {previewData.columns.map(col => (
                                                            <td key={col} className="px-3 py-1.5 whitespace-nowrap">
                                                                {col === 'ts_utc' ? new Date(row[col]).toLocaleString() :
                                                                    typeof row[col] === 'number' ? row[col].toFixed(4) : row[col]}
                                                            </td>
                                                        ))}
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}
                        </div>
                        <div>
                            <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">Data Split Policy (Train / Test / Work)</label>
                            <div className="flex gap-4 items-center bg-[#0b1121] p-2 rounded-lg border border-slate-700">
                                <div className="flex-1 flex flex-col items-center border-r border-slate-800">
                                    <span className="text-[10px] text-slate-500 mb-1">TRAIN</span>
                                    <input
                                        type="number" step="0.1"
                                        className="w-full bg-transparent text-center font-mono text-green-400 focus:outline-none"
                                        value={splitConfig.train}
                                        onChange={e => setSplitConfig({ ...splitConfig, train: parseFloat(e.target.value) })}
                                    />
                                </div>
                                <div className="flex-1 flex flex-col items-center border-r border-slate-800">
                                    <span className="text-[10px] text-slate-500 mb-1">TEST</span>
                                    <input
                                        type="number" step="0.1"
                                        className="w-full bg-transparent text-center font-mono text-blue-400 focus:outline-none"
                                        value={splitConfig.test}
                                        onChange={e => setSplitConfig({ ...splitConfig, test: parseFloat(e.target.value) })}
                                    />
                                </div>
                                <div className="flex-1 flex flex-col items-center">
                                    <span className="text-[10px] text-slate-500 mb-1">WORK</span>
                                    <input
                                        type="number" step="0.1"
                                        className="w-full bg-transparent text-center font-mono text-yellow-400 focus:outline-none"
                                        value={splitConfig.work}
                                        onChange={e => setSplitConfig({ ...splitConfig, work: parseFloat(e.target.value) })}
                                    />
                                </div>
                            </div>
                        </div>
                    </div>
                    <div className="flex justify-end pt-4 border-t border-slate-800">
                        <button
                            onClick={() => setShowNewIter(false)}
                            className="mr-4 px-4 py-2 text-slate-400 hover:text-white text-sm font-medium transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleCreateIteration}
                            disabled={!selectedDataset || validating || (validationResult && !validationResult.valid)}
                            className={`px-6 py-2 rounded-lg font-semibold text-sm transition-all shadow-lg ${!selectedDataset || validating || (validationResult && !validationResult.valid)
                                ? 'bg-slate-800 text-slate-500 cursor-not-allowed'
                                : 'bg-green-600 hover:bg-green-500 text-white hover:shadow-green-500/20'
                                }`}
                        >
                            Start Training Session
                        </button>
                    </div>
                </div>
            )}

            {/* List */}
            <div className="bg-[#0f172a] rounded-xl border border-slate-700 overflow-hidden shadow-sm">
                <table className="w-full text-left text-sm text-slate-400">
                    <thead className="bg-[#1e293b] text-slate-200 uppercase text-xs tracking-wider font-semibold">
                        <tr>
                            <th className="px-6 py-4 border-b border-slate-700">Iteration ID</th>
                            <th className="px-6 py-4 border-b border-slate-700">Dataset</th>
                            <th className="px-6 py-4 border-b border-slate-700">Status</th>
                            <th className="px-6 py-4 border-b border-slate-700 text-right">Age</th>
                            <th className="px-6 py-4 border-b border-slate-700 text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800">
                        {session.iterations?.map(iter => (
                            <tr key={iter.iteration_id} className="hover:bg-slate-800/50 transition-colors group">
                                <td className="px-6 py-4 font-mono text-xs text-purple-300 opactiy-80 group-hover:opacity-100">
                                    {iter.iteration_id.slice(0, 8)}...
                                </td>
                                <td className="px-6 py-4 text-slate-300 font-medium">
                                    {iter.dataset_name || 'Unknown Dataset'}
                                </td>
                                <td className="px-6 py-4">
                                    <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide border ${iter.status === 'COMPLETED' ? 'bg-green-500/10 text-green-400 border-green-500/20' :
                                        iter.status === 'RUNNING' ? 'bg-purple-500/10 text-purple-400 border-purple-500/20 animate-pulse' :
                                            iter.status === 'FAILED' ? 'bg-red-500/10 text-red-400 border-red-500/20' :
                                                'bg-slate-700/50 text-slate-400 border-slate-600'
                                        }`}>
                                        {iter.status || 'PENDING'}
                                    </span>
                                </td>
                                <td className="px-6 py-4 text-right text-xs">
                                    {iter.start_utc ? new Date(iter.start_utc).toLocaleDateString() : 'Not started'}
                                </td>
                                <td className="px-6 py-4 text-right">
                                    <div className="flex items-center justify-end gap-2">
                                        {(iter.status === 'COMPLETED' || iter.status === 'FAILED') && (
                                            <button
                                                onClick={() => handleRerunIteration(iter)}
                                                className="text-green-400 hover:text-green-300 font-medium text-xs flex items-center gap-1 transition-colors"
                                                title="Re-run this iteration"
                                            >
                                                <Play size={12} /> Re-run
                                            </button>
                                        )}
                                        <button
                                            onClick={() => setSelectedIterationId(iter.iteration_id)}
                                            className={`text-xs font-medium flex items-center gap-1 transition-colors ${selectedIterationId === iter.iteration_id ? 'text-blue-300' : 'text-blue-400 hover:text-blue-300'}`}
                                            title="Show backend logs"
                                        >
                                            Logs
                                        </button>
                                        <button
                                            onClick={() => navigate(`/ml/studio/session/${sessionId}/run/${iter.iteration_id}`)}
                                            className="text-purple-400 hover:text-purple-300 font-medium text-xs flex items-center justify-end gap-1 ml-auto group-hover:translate-x-1 transition-transform"
                                        >
                                            Console <ArrowLeft size={12} className="rotate-180" />
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        ))}
                        {(!session.iterations || session.iterations.length === 0) && (
                            <tr>
                                <td colSpan="5" className="px-6 py-12 text-center">
                                    <div className="flex flex-col items-center justify-center text-slate-500 gap-2">
                                        <Database size={32} className="opacity-20" />
                                        <p>No iterations found for this session.</p>
                                        <button
                                            onClick={() => setShowNewIter(true)}
                                            className="text-purple-400 hover:text-purple-300 text-xs font-medium mt-2"
                                        >
                                            Launch your first run
                                        </button>
                                    </div>
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            <div className="mt-6 bg-slate-950 rounded-xl border border-slate-800 p-4 font-mono text-xs">
                <div className="flex items-center justify-between mb-2">
                    <div className="text-slate-500 uppercase tracking-wider text-[10px]">
                        Backend Logs (ML Core)
                        {selectedIterationId && (
                            <span className="text-slate-600 ml-2">#{selectedIterationId.slice(0, 8)}</span>
                        )}
                    </div>
                    <div className="flex items-center gap-3">
                        <span className="text-[10px] text-slate-600">{iterationLogs.length} lines</span>
                        <button
                            onClick={() => fetchIterationLogs(selectedIterationId)}
                            disabled={!selectedIterationId || logsLoading}
                            className="p-1.5 text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-slate-800/60 disabled:opacity-50"
                            title="Refresh logs"
                        >
                            <RefreshCw size={12} />
                        </button>
                    </div>
                </div>

                {!selectedIterationId && (
                    <div className="text-slate-700 italic">Select an iteration to view backend logs.</div>
                )}

                {selectedIterationId && logsLoading && (
                    <div className="text-slate-600 italic">Loading logs...</div>
                )}

                {selectedIterationId && logsError && (
                    <div className="text-red-400">{logsError}</div>
                )}

                {selectedIterationId && !logsLoading && !logsError && (
                    <div className="space-y-1">
                        {iterationLogs.length === 0 && (
                            <div className="text-slate-700 italic">No logs yet for this iteration.</div>
                        )}
                        {iterationLogs.map((log, i) => {
                            const isError = log.includes("ERROR") || log.includes("Exception") || log.includes("Traceback");
                            return (
                                <pre
                                    key={`${selectedIterationId}-${i}`}
                                    className={`border-l-2 pl-2 whitespace-pre-wrap break-words ${isError ? 'text-red-400 border-red-500 bg-red-900/10' : 'text-slate-400 border-slate-800'}`}
                                >
                                    {log}
                                </pre>
                            );
                        })}
                    </div>
                )}
            </div>

        </div>
    );
};

export default MlSessionDetail;
