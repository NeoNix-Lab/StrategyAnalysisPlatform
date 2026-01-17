
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Play, Activity, Clock, ArrowLeft, Terminal, RefreshCw, BarChart2 } from 'lucide-react';
import TrainingCharts from './components/TrainingCharts';

const MlTrainingRun = () => {
    const { sessionId, iterationId } = useParams();
    const navigate = useNavigate();

    const LOG_VERBOSITY_PRESETS = [
        { label: 'Low', value: 5000 },
        { label: 'Normal', value: 2000 },
        { label: 'High', value: 200 }
    ];

    // State for verbosity
    const [verbose, setVerbose] = useState(false);
    const [errorMsg, setErrorMsg] = useState(null);
    const [logEverySteps, setLogEverySteps] = useState(2000);
    const [logVerbosityStatus, setLogVerbosityStatus] = useState(null);
    const [logVerbositySaving, setLogVerbositySaving] = useState(false);

    const [iteration, setIteration] = useState(null);
    const [status, setStatus] = useState('LOADING');
    const [logs, setLogs] = useState([]);

    // Chart Data Source (Real Metrics)
    const [historyMetrics, setHistoryMetrics] = useState([]);
    const [equityData, setEquityData] = useState([]);

    const [hasInferenceHistory, setHasInferenceHistory] = useState(false);

    const fetchStatus = async () => {
        try {
            // Fetch specific iteration details (including metrics)
            const res = await fetch(`http://localhost:8000/api/ml/studio/iterations/${iterationId}`);
            if (!res.ok) throw new Error("Failed to fetch iteration");

            const iter = await res.json();
            setIteration(iter);
            setStatus(iter.status);

            // Parse metrics for error and history
            let rawMetrics = iter.metrics_json;
            if (typeof rawMetrics === 'string') {
                try { rawMetrics = JSON.parse(rawMetrics); } catch (e) { console.error("JSON Parse Error", e); }
            }

            if (rawMetrics) {
                if (rawMetrics.error) {
                    setErrorMsg(rawMetrics.error);
                }
                if (rawMetrics.history) {
                    setHistoryMetrics(rawMetrics.history);
                }
                if (rawMetrics.inference_history_path) {
                    setHasInferenceHistory(true);
                }
            }

            // [NEW] Fetch Metrics (Equity Curve) - SUSPENDED (Endpoint missing)
            /*
            try {
                const metricsRes = await fetch(`http://localhost:8000/api/metrics/run/${iterationId}`);
                if (metricsRes.ok) {
                    const metrics = await metricsRes.json();
                    if (metrics.equity_curve) {
                        setEquityData(metrics.equity_curve);
                    }
                }
            } catch (ignore) { console.warn("Metrics fetch failed", ignore); }
            */

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

    const applyLogVerbosity = async (steps) => {
        if (!iterationId) return;
        setLogVerbositySaving(true);
        setLogVerbosityStatus(null);
        try {
            const res = await fetch(`http://localhost:8000/api/ml/studio/iterations/${iterationId}/logging`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ log_every_steps: steps })
            });
            if (!res.ok) throw new Error("Failed to update logging");
            const data = await res.json();
            if (data && typeof data.log_every_steps === 'number') {
                setLogEverySteps(data.log_every_steps);
            }
            setLogVerbosityStatus('Applied');
        } catch (err) {
            console.error(err);
            setLogVerbosityStatus('Failed');
        } finally {
            setLogVerbositySaving(false);
        }
    };

    // 1. Reset State on ID change
    useEffect(() => {
        setIteration(null);
        setStatus('LOADING');
        setLogs([]);
        setHistoryMetrics([]);
        setEquityData([]);
        setErrorMsg(null);
        fetchStatus(); // Initial fetch
        setLogVerbosityStatus(null);
    }, [sessionId, iterationId]);

    // 2. Poll based on status
    useEffect(() => {
        let interval;
        if (status === 'RUNNING' || status === 'QUEUED' || status === 'LOADING' || status === 'PENDING') {
            interval = setInterval(fetchStatus, 10000);
        }
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [status]);


    const handleStart = async () => {
        try {
            await fetch(`http://localhost:8000/api/ml/studio/iterations/${iterationId}/run`, { method: 'POST' });
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

    // Backtest Modal State
    const [showBacktestModal, setShowBacktestModal] = useState(false);
    const [backtestDatasetId, setBacktestDatasetId] = useState("");
    const [isSubmittingTest, setIsSubmittingTest] = useState(false);

    const handleBacktestClick = () => {
        // Default to current dataset if not set
        if (!backtestDatasetId && iteration) {
            setBacktestDatasetId(iteration.dataset_id);
        }
        setShowBacktestModal(true);
    };

    const handleViewResults = async () => {
        try {
            const res = await fetch(`http://localhost:8000/api/ml/studio/iterations/${iterationId}/reconstruct`, { method: 'POST' });
            if (!res.ok) throw new Error("Reconstruction failed");
            const data = await res.json();
            window.open(`/strategies/runs/${data.run_id}`, '_blank');
        } catch (err) {
            alert("Failed to view results: " + err.message);
        }
    };

    const handleRunBacktest = async () => {
        if (!iteration) return;
        setIsSubmittingTest(true);
        try {
            const body = {
                target_dataset_id: backtestDatasetId,
                source_iteration_id: iterationId,
                split_config: { train: 0, test: 1.0, work: 0 } // Full range or custom
            };

            const res = await fetch(`http://localhost:8000/api/ml/studio/test`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (!res.ok) throw new Error("Failed to start backtest");

            const newRun = await res.json();
            // Navigate to the new Test Run (which is just an iteration)
            navigate(`/ml/studio/session/${iteration.session_id}/run/${newRun.iteration_id}`);
        } catch (err) {
            alert("Error starting backtest: " + err.message);
        } finally {
            setIsSubmittingTest(false);
            setShowBacktestModal(false);
        }
    };

    if (!iteration && status === 'LOADING') return <div className="p-8 text-slate-400">Loading...</div>;

    return (
        <div className="p-6 h-[calc(100vh-64px)] flex flex-col text-slate-200 relative">
            {/* Backtest Modal */}
            {showBacktestModal && (
                <div className="absolute inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
                    <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl w-full max-w-md shadow-2xl">
                        <h3 className="text-xl font-bold text-slate-200 mb-4">Run Backtest</h3>
                        <div className="flex justify-end gap-3 mt-8">
                            <button
                                onClick={() => setShowBacktestModal(false)}
                                className="px-4 py-2 text-slate-400 hover:text-slate-200 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleRunBacktest}
                                disabled={isSubmittingTest}
                                className="bg-blue-600 hover:bg-blue-500 text-white px-6 py-2 rounded-lg font-medium flex items-center gap-2"
                            >
                                {isSubmittingTest ? 'Starting...' : 'Launch Backtest'}
                            </button>
                        </div>
                    </div>
                </div >
            )}

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
                    <button
                        onClick={fetchStatus}
                        className="p-2 text-slate-400 hover:text-white transition-colors rounded-lg hover:bg-slate-700/50"
                        title="Refresh Status"
                    >
                        <RefreshCw size={16} />
                    </button>
                    <div className="flex items-center gap-2 text-sm text-slate-400">
                        <span className="text-xs text-slate-500">Log Verbosity</span>
                        <select
                            className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs text-slate-200 focus:border-purple-500 outline-none"
                            value={logEverySteps}
                            onChange={(e) => applyLogVerbosity(parseInt(e.target.value))}
                            disabled={logVerbositySaving}
                        >
                            {LOG_VERBOSITY_PRESETS.map((preset) => (
                                <option key={preset.value} value={preset.value}>{preset.label}</option>
                            ))}
                        </select>
                        {logVerbosityStatus && (
                            <span className={`text-[10px] ${logVerbosityStatus === 'Applied' ? 'text-green-400' : 'text-red-400'}`}>
                                {logVerbosityStatus}
                            </span>
                        )}
                    </div>
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

                    {/* ACTION BUTTONS */}
                    {status === 'PENDING' && (
                        <button
                            onClick={handleStart}
                            className="bg-green-600 hover:bg-green-500 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-lg shadow-green-500/20 transition-all"
                        >
                            <Play size={16} fill="currentColor" /> Start Run
                        </button>
                    )}

                    {(status === 'COMPLETED' || status === 'FAILED' || status === 'CANCELLED') && (
                        <>
                            <button
                                onClick={handleStart}
                                className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-lg shadow-purple-500/20 transition-all"
                            >
                                <Activity size={16} /> Repeat Run
                            </button>

                            {/* NEW BACKTEST BUTTON */}
                            {status === 'COMPLETED' && (
                                <button
                                    onClick={handleBacktestClick}
                                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-lg shadow-blue-500/20 transition-all ml-2"
                                >
                                    <Activity size={16} /> Run Backtest
                                </button>
                            )}

                            {status === 'COMPLETED' && hasInferenceHistory && (
                                <button
                                    onClick={handleViewResults}
                                    className="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-2 rounded-lg font-medium flex items-center gap-2 shadow-lg shadow-emerald-500/20 transition-all ml-2"
                                >
                                    <BarChart2 size={16} /> View Results
                                </button>
                            )}
                        </>
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
            {
                errorMsg && (
                    <div className="mb-6 bg-red-500/10 border border-red-500/50 p-4 rounded-xl text-red-200 font-mono text-sm overflow-x-auto whitespace-pre-wrap">
                        <strong className="block text-red-400 mb-1">CRITICAL ERROR:</strong>
                        {errorMsg}
                    </div>
                )
            }

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-1 min-h-0">
                {/* Main Chart Area */}
                <div className="lg:col-span-2 bg-slate-800 rounded-xl border border-slate-700 p-4 flex flex-col">
                    <h3 className="text-sm font-medium text-slate-400 mb-4 flex items-center gap-2">
                        <Activity size={16} className="text-blue-400" />
                        Live Metrics
                    </h3>

                    {/* Charts Component handles empty states internally */}
                    <div className="flex-1 min-h-0 relative">
                        <TrainingCharts data={historyMetrics} equityData={equityData} />
                    </div>

                    {/* DEBUG RAW DATA */}
                    {verbose && (
                        <div className="mt-4 p-2 bg-slate-900 rounded border border-slate-700 text-[10px] font-mono whitespace-pre-wrap overflow-auto max-h-40">
                            <strong>DEBUG DATA STATE:</strong>
                            <br />History Len: {historyMetrics?.length}
                            <br />Equity Len: {equityData?.length}
                            <br />Sample: {JSON.stringify(historyMetrics?.[0] || "No Data")}
                            <br />Raw Metrics: {JSON.stringify(historyMetrics)}
                        </div>
                    )}
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
        </div >
    );
};

export default MlTrainingRun;
