import React, { useState, useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Database, Clock, Plus, Zap, RefreshCw, Brain, Settings, Code, ChevronDown, ChevronUp } from 'lucide-react';
import api from '../../api/axios';

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

    // UI State
    const [expandedSection, setExpandedSection] = useState(null); // 'model' | 'process' | 'function' | null

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
            api.get(`/ml/studio/functions/${session.function.id}`)
                .then(res => setRewardCode(res.data.code))
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
            const res = await api.post(`/datasets/${selectedDataset}/preview`, { limit: 5, offset: 0 });
            setPreviewData(res.data);
        } catch (err) {
            console.error("Preview fetch failed", err);
        }
    };

    const validateRewardOnDataset = async () => {
        setValidating(true);
        setValidationResult(null);
        try {
            const res = await api.post('/ml/studio/functions/validate', {
                code: rewardCode,
                dataset_id: selectedDataset,
            });
            setValidationResult(res.data);
        } catch (err) {
            console.error(err);
            setValidationResult({ valid: false, error: "Validation request failed" });
        } finally {
            setValidating(false);
        }
    };

    useEffect(() => {
        Promise.all([
            api.get(`/ml/studio/sessions/${sessionId}`).then(res => res.data),
            api.get('/datasets').then(res => res.data)
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
                const res = await api.get(`/ml/studio/sessions/${sessionId}`);
                const sessionData = res.data;
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
            await api.post('/ml/studio/iterations', {
                session_id: sessionId,
                dataset_id: selectedDataset,
                split_config: splitConfig
            });

            // Refresh session or navigate? Maybe stay and show the new iteration
            // For now, reload
            window.location.reload();
        } catch (err) {
            console.error(err);
        }
    };

    const handleRerunIteration = async (iteration) => {
        if (!window.confirm(`Are you sure you want to re-run this iteration on ${iteration.dataset_name}?`)) {
            return;
        }

        try {
            await api.post(`/ml/studio/iterations/${iteration.iteration_id}/run`);

            // Refresh the session data to show updated status
            const sessionRes = await api.get(`/ml/studio/sessions/${sessionId}`);
            setSession(sessionRes.data);
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
            const res = await api.get(`/ml/studio/iterations/${iterationId}/logs?limit=500`);
            const data = res.data;
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

            {/* Header / Config Cards */}
            <div className="mb-8 grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* 1. Model Card */}
                <div
                    onClick={() => setExpandedSection(expandedSection === 'model' ? null : 'model')}
                    className={`
                        relative overflow-hidden rounded-xl border transition-all duration-300 cursor-pointer group
                        ${expandedSection === 'model'
                            ? 'bg-slate-900/90 border-blue-500/50 shadow-[0_0_30px_-5px_rgba(59,130,246,0.3)] col-span-1 lg:col-span-3'
                            : 'bg-[#0f172a] border-slate-700 hover:border-slate-500 hover:shadow-lg'
                        }
                    `}
                >
                    <div className="absolute top-0 right-0 p-24 bg-blue-500/5 blur-[80px] rounded-full pointer-events-none"></div>

                    <div className="p-6 relative z-10">
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-4">
                                <div className={`
                                    p-3 rounded-xl border transition-colors
                                    ${expandedSection === 'model'
                                        ? 'bg-blue-500/20 border-blue-500/30'
                                        : 'bg-slate-800 border-slate-700 group-hover:border-slate-600'
                                    }
                                `}>
                                    <Brain size={24} className={expandedSection === 'model' ? 'text-blue-400' : 'text-slate-400'} />
                                </div>
                                <div>
                                    <div className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-0.5">Model Architecture</div>
                                    <div className="text-lg font-bold text-slate-200 group-hover:text-white transition-colors">
                                        {session.model?.name || 'Unknown Model'}
                                    </div>
                                </div>
                            </div>
                            {expandedSection === 'model' ? <ChevronUp size={20} className="text-slate-500" /> : <ChevronDown size={20} className="text-slate-600" />}
                        </div>

                        {/* Expanded Content */}
                        {expandedSection === 'model' && session.model && (
                            <div className="mt-6 pt-6 border-t border-slate-800 animate-in fade-in slide-in-from-top-2 duration-300">
                                <p className="text-slate-400 text-sm mb-6 max-w-3xl leading-relaxed">
                                    {session.model.description || "No description provided for this architecture."}
                                </p>

                                <div className="bg-[#0b1121] rounded-lg border border-slate-800 p-4">
                                    <div className="text-xs font-mono text-blue-400 mb-3 uppercase tracking-wider">Layer Configuration</div>
                                    <div className="space-y-2">
                                        {session.model.layers_json ? (
                                            Array.isArray(session.model.layers_json) ? (
                                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
                                                    {session.model.layers_json.map((layer, idx) => (
                                                        <div key={idx} className="bg-slate-800/50 p-3 rounded border border-slate-700/50 flex flex-col gap-1">
                                                            <div className="text-xs font-bold text-slate-300">{layer.type || 'Layer'}</div>
                                                            <div className="text-[10px] text-slate-500 font-mono overflow-hidden text-ellipsis whitespace-nowrap">
                                                                {Object.entries(layer).map(([k, v]) => k !== 'type' ? `${k}:${v} ` : '').join('')}
                                                            </div>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <pre className="text-xs text-slate-500 overflow-x-auto">{JSON.stringify(session.model.layers_json, null, 2)}</pre>
                                            )
                                        ) : (
                                            <div className="text-slate-600 italic text-sm">No explicit layer configuration found.</div>
                                        )}
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* 2. Process Card */}
                <div
                    onClick={() => setExpandedSection(expandedSection === 'process' ? null : 'process')}
                    className={`
                        relative overflow-hidden rounded-xl border transition-all duration-300 cursor-pointer group
                        ${expandedSection === 'process'
                            ? 'bg-slate-900/90 border-green-500/50 shadow-[0_0_30px_-5px_rgba(34,197,94,0.3)] col-span-1 lg:col-span-3'
                            : 'bg-[#0f172a] border-slate-700 hover:border-slate-500 hover:shadow-lg'
                        }
                    `}
                >
                    <div className="absolute top-0 right-0 p-24 bg-green-500/5 blur-[80px] rounded-full pointer-events-none"></div>

                    <div className="p-6 relative z-10">
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-4">
                                <div className={`
                                    p-3 rounded-xl border transition-colors
                                    ${expandedSection === 'process'
                                        ? 'bg-green-500/20 border-green-500/30'
                                        : 'bg-slate-800 border-slate-700 group-hover:border-slate-600'
                                    }
                                `}>
                                    <Settings size={24} className={expandedSection === 'process' ? 'text-green-400' : 'text-slate-400'} />
                                </div>
                                <div>
                                    <div className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-0.5">Training Process</div>
                                    <div className="text-lg font-bold text-slate-200 group-hover:text-white transition-colors">
                                        {session.process?.name || 'Default Process'}
                                    </div>
                                </div>
                            </div>
                            {expandedSection === 'process' ? <ChevronUp size={20} className="text-slate-500" /> : <ChevronDown size={20} className="text-slate-600" />}
                        </div>

                        {/* Expanded Content */}
                        {expandedSection === 'process' && session.process && (
                            <div className="mt-6 pt-6 border-t border-slate-800 animate-in fade-in slide-in-from-top-2 duration-300">
                                <p className="text-slate-400 text-sm mb-6 max-w-3xl leading-relaxed">
                                    {session.process.description || "Standard training process configuration."}
                                </p>

                                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                                    {[
                                        { label: 'Optimizer', value: session.process.optimizer, color: 'text-purple-400' },
                                        { label: 'Loss Function', value: session.process.loss, color: 'text-red-400' },
                                        { label: 'Learning Rate', value: session.process.learning_rate, color: 'text-yellow-400' },
                                        { label: 'Batch Size', value: session.process.batch_size, color: 'text-blue-400' },
                                        { label: 'Epochs', value: session.process.epochs, color: 'text-green-400' },
                                        { label: 'Gamma', value: session.process.gamma, color: 'text-orange-400' },
                                        { label: 'Epsilon Start', value: session.process.epsilon_start, color: 'text-pink-400' },
                                        { label: 'Epsilon End', value: session.process.epsilon_end, color: 'text-pink-400' },
                                        { label: 'Decay Function', value: session.process.decay_function, color: 'text-pink-400' },
                                        { label: 'Decay Scope', value: session.process.decay_scope, color: 'text-pink-400' },
                                        { label: 'Force Steps', value: session.process.force_decay_steps, color: 'text-pink-400' },
                                        { label: 'Decay Rate', value: session.process.epsilon_decay, color: 'text-pink-400' },
                                        { label: 'Window Size', value: session.process.window_size, color: 'text-cyan-400' },
                                    ].map((item, i) => (
                                        <div key={i} className="bg-[#0b1121] p-3 rounded-lg border border-slate-800">
                                            <div className="text-[10px] uppercase text-slate-500 font-semibold mb-1">{item.label}</div>
                                            <div className={`font-mono font-medium ${item.color}`}>{item.value !== null ? item.value : '-'}</div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                {/* 3. Function Card */}
                <div
                    onClick={() => setExpandedSection(expandedSection === 'function' ? null : 'function')}
                    className={`
                        relative overflow-hidden rounded-xl border transition-all duration-300 cursor-pointer group
                        ${expandedSection === 'function'
                            ? 'bg-slate-900/90 border-purple-500/50 shadow-[0_0_30px_-5px_rgba(168,85,247,0.3)] col-span-1 lg:col-span-3'
                            : 'bg-[#0f172a] border-slate-700 hover:border-slate-500 hover:shadow-lg'
                        }
                    `}
                >
                    <div className="absolute top-0 right-0 p-24 bg-purple-500/5 blur-[80px] rounded-full pointer-events-none"></div>

                    <div className="p-6 relative z-10">
                        <div className="flex items-start justify-between">
                            <div className="flex items-center gap-4">
                                <div className={`
                                    p-3 rounded-xl border transition-colors
                                    ${expandedSection === 'function'
                                        ? 'bg-purple-500/20 border-purple-500/30'
                                        : 'bg-slate-800 border-slate-700 group-hover:border-slate-600'
                                    }
                                `}>
                                    <Code size={24} className={expandedSection === 'function' ? 'text-purple-400' : 'text-slate-400'} />
                                </div>
                                <div>
                                    <div className="text-xs uppercase tracking-wider font-semibold text-slate-500 mb-0.5">Reward Function</div>
                                    <div className="text-lg font-bold text-slate-200 group-hover:text-white transition-colors">
                                        {session.function?.name || 'Custom Logic'}
                                    </div>
                                </div>
                            </div>
                            {expandedSection === 'function' ? <ChevronUp size={20} className="text-slate-500" /> : <ChevronDown size={20} className="text-slate-600" />}
                        </div>

                        {/* Expanded Content */}
                        {expandedSection === 'function' && session.function && (
                            <div className="mt-6 pt-6 border-t border-slate-800 animate-in fade-in slide-in-from-top-2 duration-300">
                                <p className="text-slate-400 text-sm mb-6 max-w-3xl leading-relaxed">
                                    {session.function.description || "No description provided for this reward function."}
                                </p>

                                {/* Metadata Parsing */}
                                {(() => {
                                    let meta = {};
                                    try {
                                        meta = session.function.metadata_json
                                            ? (typeof session.function.metadata_json === 'string'
                                                ? JSON.parse(session.function.metadata_json)
                                                : session.function.metadata_json)
                                            : {};
                                    } catch (e) {
                                        console.error("Failed to parse function metadata", e);
                                    }

                                    const actionLabels = meta.action_labels || [];
                                    const statusLabels = meta.status_labels || [];
                                    const execParams = meta.execution_params || {};
                                    const transitionMatrix = execParams.transition_matrix || {};
                                    const forceExitMap = execParams.force_exit_map || {};

                                    return (
                                        <div className="space-y-6">

                                            {/* Spaces Config */}
                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                <div className="bg-[#0b1121] rounded-lg border border-slate-800 p-4">
                                                    <div className="text-xs uppercase tracking-wider text-slate-500 font-bold mb-3">Action Space</div>
                                                    <div className="flex flex-wrap gap-2">
                                                        {actionLabels.length > 0 ? actionLabels.map((lbl, i) => (
                                                            <span key={i} className="px-2 py-1 bg-slate-800 rounded border border-slate-700 text-xs font-mono text-blue-300">
                                                                {lbl} <span className="text-slate-600 ml-1">({i})</span>
                                                            </span>
                                                        )) : <span className="text-slate-600 italic text-xs">Default (HOLD, BUY, SELL)</span>}
                                                    </div>
                                                </div>
                                                <div className="bg-[#0b1121] rounded-lg border border-slate-800 p-4">
                                                    <div className="text-xs uppercase tracking-wider text-slate-500 font-bold mb-3">Status Space</div>
                                                    <div className="flex flex-wrap gap-2">
                                                        {statusLabels.length > 0 ? statusLabels.map((lbl, i) => (
                                                            <span key={i} className="px-2 py-1 bg-slate-800 rounded border border-slate-700 text-xs font-mono text-purple-300">
                                                                {lbl} <span className="text-slate-600 ml-1">({i})</span>
                                                            </span>
                                                        )) : <span className="text-slate-600 italic text-xs">Default (FLAT, LONG, SHORT)</span>}
                                                    </div>
                                                </div>
                                            </div>

                                            {/* FSM Matrix */}
                                            {Object.keys(transitionMatrix).length > 0 && (
                                                <div className="bg-[#0b1121] rounded-lg border border-slate-800 overflow-hidden">
                                                    <div className="px-4 py-3 border-b border-slate-800 bg-slate-900/50 flex justify-between items-center">
                                                        <span className="text-xs font-bold text-slate-400 uppercase tracking-wider flex items-center gap-2">
                                                            <Settings size={12} /> Execution Logic (FSM)
                                                        </span>
                                                        <span className="text-[10px] text-slate-500 font-mono">Price Column: {execParams.price_column || 'close'}</span>
                                                    </div>
                                                    <div className="overflow-x-auto">
                                                        <table className="w-full text-left border-collapse">
                                                            <thead>
                                                                <tr className="bg-slate-900/30">
                                                                    <th className="p-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-800">State</th>
                                                                    <th className="p-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-800">Action</th>
                                                                    <th className="p-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-800">Next State</th>
                                                                    <th className="p-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-800">Effect</th>
                                                                    <th className="p-3 text-[10px] font-bold text-slate-500 uppercase tracking-wider border-b border-slate-800 text-center">Update Price</th>
                                                                </tr>
                                                            </thead>
                                                            <tbody className="divide-y divide-slate-800/50">
                                                                {(meta.status_labels || ["FLAT", "LONG", "SHORT"]).map(status => (
                                                                    <React.Fragment key={status}>
                                                                        {(meta.action_labels || ["HOLD", "BUY", "SELL"]).map((action, idx) => {
                                                                            const config = transitionMatrix[status]?.[action];
                                                                            if (!config) return null;

                                                                            const isDefault = config.next_state === status && config.effect === 'NONE' && !config.update_price;

                                                                            return (
                                                                                <tr key={`${status}-${action}`} className={`hover:bg-slate-800/30 transition-colors ${isDefault ? 'opacity-60 hover:opacity-100' : ''}`}>
                                                                                    {idx === 0 && (
                                                                                        <td rowSpan={(meta.action_labels || ["HOLD", "BUY", "SELL"]).length} className="p-3 text-xs font-mono text-slate-400 border-r border-slate-800 align-top bg-slate-900/20">
                                                                                            {status}
                                                                                        </td>
                                                                                    )}
                                                                                    <td className="p-3 text-xs font-mono text-blue-300/80 pl-4">{action}</td>
                                                                                    <td className="p-3 text-xs text-slate-300 font-medium">
                                                                                        {config.next_state !== status ? <span className="text-purple-400">{config.next_state}</span> : <span className="text-slate-600">{status}</span>}
                                                                                    </td>
                                                                                    <td className="p-3 text-xs text-slate-300">
                                                                                        {config.effect !== 'NONE' ? <span className="text-orange-400 font-mono text-[10px]">{config.effect}</span> : <span className="text-slate-700">-</span>}
                                                                                    </td>
                                                                                    <td className="p-3 text-center">
                                                                                        {config.update_price ? <div className="w-1.5 h-1.5 rounded-full bg-green-500 mx-auto"></div> : null}
                                                                                    </td>
                                                                                </tr>
                                                                            );
                                                                        })}
                                                                    </React.Fragment>
                                                                ))}
                                                            </tbody>
                                                        </table>
                                                    </div>
                                                </div>
                                            )}

                                            {/* Termination Policy */}
                                            {Object.keys(forceExitMap).length > 0 && (
                                                <div className="bg-red-900/10 rounded-lg border border-red-900/30 overflow-hidden">
                                                    <div className="px-4 py-2 border-b border-red-900/20 bg-red-900/20 flex items-center gap-2">
                                                        <span className="text-xs font-bold text-red-300 uppercase tracking-wider">Termination Policy</span>
                                                        <span className="text-[10px] text-red-400/60">(Force Exit)</span>
                                                    </div>
                                                    <div className="p-3 grid grid-cols-2 md:grid-cols-4 gap-3">
                                                        {Object.entries(forceExitMap).map(([statusIdx, actionIdx]) => {
                                                            const sLabel = (meta.status_labels || [])[statusIdx] || statusIdx;
                                                            const aLabel = (meta.action_labels || [])[actionIdx] || actionIdx;
                                                            return (
                                                                <div key={statusIdx} className="bg-slate-900/50 p-2 rounded border border-red-500/10 flex items-center justify-between">
                                                                    <span className="text-xs font-mono text-slate-400">{sLabel}</span>
                                                                    <span className="text-xs text-slate-600">→</span>
                                                                    <span className="text-xs font-mono text-red-400">{aLabel}</span>
                                                                </div>
                                                            );
                                                        })}
                                                    </div>
                                                </div>
                                            )}

                                        </div>
                                    );
                                })()}

                                <div className="mt-6 bg-[#0b1121] rounded-lg border border-slate-800 overflow-hidden">
                                    <div className="flex items-center justify-between px-4 py-2 bg-slate-900 border-b border-slate-800">
                                        <span className="text-xs font-mono text-purple-400 flex items-center gap-2">
                                            <Code size={12} /> Source Code
                                        </span>
                                    </div>
                                    <div className="p-4 overflow-x-auto">
                                        <pre className="text-xs font-mono text-slate-300 leading-relaxed">
                                            {session.function.code || "// No code available"}
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        )}
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
