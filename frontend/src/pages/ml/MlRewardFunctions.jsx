import React, { useState, useEffect, useRef } from 'react';
import { Plus, Save, Trash2, Code, Play, CheckCircle, XCircle, Database, Settings } from 'lucide-react';
import RewardEditor from './components/RewardEditor';
import '../Dashboard.css';

const MlRewardFunctions = () => {
    const [functions, setFunctions] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [editMode, setEditMode] = useState(false); // false = list/view, true = edit/create
    const [loading, setLoading] = useState(true);

    // Form State
    const [name, setName] = useState('');
    const [code, setCode] = useState('');
    const [description, setDescription] = useState('');

    // Explicit Space Definition State
    const [actionLabels, setActionLabels] = useState("HOLD, BUY, SELL");
    const [statusLabels, setStatusLabels] = useState("FLAT, LONG, SHORT");
    const [showConfig, setShowConfig] = useState(false);

    // Validation Context
    const [datasets, setDatasets] = useState([]);
    const [selectedDatasetId, setSelectedDatasetId] = useState('');
    const [validationResult, setValidationResult] = useState(null); // { valid: bool, result: float, error: string }

    const editorRef = useRef(null); // Stores Monaco instance

    const DEFAULT_CODE = `def calculate_reward(env, action):
    # 'env.data' contains the current step's market data (dict)
    # Example: Accessing close price
    # current_close = env.data['close'] 
    
    # 'env' object exposes state and configured spaces
    # action is an integer index from env.action_labels
    # pos = env.position (index from env.status_labels)
    
    # Use explicit namespaces instead of magic numbers:
    # if action == env.actions.BUY: ...
    # if env.position == env.status.LONG: ...
    
    reward = 0
    # Your logic here...
    
    return reward
`;

    useEffect(() => {
        fetchFunctions();
        fetchDatasets();
    }, []);

    const fetchFunctions = async () => {
        try {
            const res = await fetch('/api/ml/studio/functions');
            if (res.ok) setFunctions(await res.json());
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const fetchDatasets = async () => {
        try {
            const res = await fetch('/api/datasets/');
            if (res.ok) setDatasets(await res.json());
        } catch (e) { console.error(e); }
    };

    const handleSelect = async (id) => {
        setLoading(true);
        try {
            const res = await fetch(`/api/ml/studio/functions/${id}`);
            if (res.ok) {
                const data = await res.json();
                setSelectedId(id);
                setName(data.name);
                setCode(data.code);
                setDescription(data.description || '');

                // Parse metadata
                const meta = data.metadata_json || {};
                setActionLabels((meta.action_labels || ["HOLD", "BUY", "SELL"]).join(", "));
                setStatusLabels((meta.status_labels || ["FLAT", "LONG", "SHORT"]).join(", "));

                setEditMode(true); // Auto switch to edit/view mode
                setValidationResult(null);
                setShowConfig(false);
            }
        } finally { setLoading(false); }
    };

    const handleCreateNew = () => {
        setSelectedId(null);
        setName('New Reward Function');
        setCode(DEFAULT_CODE);
        setDescription('');
        setActionLabels("HOLD, BUY, SELL");
        setStatusLabels("FLAT, LONG, SHORT");
        setEditMode(true);
        setValidationResult(null);
        setShowConfig(false);
    };

    const getMetadataPayload = () => {
        return {
            metadata_json: {
                action_labels: actionLabels.split(",").map(s => s.trim()).filter(s => s),
                status_labels: statusLabels.split(",").map(s => s.trim()).filter(s => s)
            }
        };
    };

    const handleValidate = async () => {
        if (!selectedDatasetId) {
            alert("Please select a reference dataset to validate against.");
            return;
        }
        setValidationResult(null);
        try {
            const payload = {
                code,
                dataset_id: selectedDatasetId,
                ...getMetadataPayload()
            };

            const res = await fetch('/api/ml/studio/functions/validate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await res.json();
            setValidationResult(data);
        } catch (e) {
            setValidationResult({ valid: false, error: "Network error during validation" });
        }
    };

    const handleSave = async () => {
        const payload = {
            name,
            code,
            description,
            ...getMetadataPayload()
        };
        try {
            const res = await fetch('/api/ml/studio/functions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                await fetchFunctions();
                setEditMode(false);
                setSelectedId(null); // Return to list
            } else {
                alert("Failed to save");
            }
        } catch (e) { console.error(e); }
    };

    const handleEditorMount = (editor, monaco) => {
        editorRef.current = editor;
    };

    const insertVariable = (varName, isEnv = false) => {
        if (editorRef.current) {
            const textToInsert = isEnv ? `${varName}` : `env.data['${varName}']`;
            const selection = editorRef.current.getSelection();
            const id = { major: 1, minor: 1 };
            const op = { identifier: id, range: selection, text: textToInsert, forceMoveMarkers: true };
            editorRef.current.executeEdits("my-source", [op]);
            editorRef.current.focus();
        } else {
            // Fallback if editor not mounted yet (rare)
            setCode(prev => prev + (isEnv ? `${varName}` : `env.data['${varName}']`));
        }
    };

    // Derived state for schema hints
    const selectedDataset = datasets.find(d => d.dataset_id === selectedDatasetId);
    const availableColumns = selectedDataset?.feature_config || [];

    // Parse labels for UI hints
    const actionList = actionLabels.split(",").map(s => s.trim()).filter(s => s);
    const statusList = statusLabels.split(",").map(s => s.trim()).filter(s => s);

    return (
        <div style={{ display: 'grid', gridTemplateColumns: '250px 1fr', gap: '2rem', height: 'calc(100vh - 140px)' }}>

            {/* Left Panel: List */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: '0', overflow: 'hidden' }}>
                <div style={{ padding: '1rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ margin: 0, fontSize: '1rem' }}>Functions</h3>
                    <button onClick={handleCreateNew} style={{ background: 'transparent', border: 'none', color: '#60a5fa', cursor: 'pointer' }}>
                        <Plus size={18} />
                    </button>
                </div>
                <div style={{ overflowY: 'auto', flex: 1 }}>
                    {loading && !selectedId ? (
                        <div style={{ padding: '1rem', color: '#64748b' }}>Loading...</div>
                    ) : (
                        functions.map(f => (
                            <div
                                key={f.function_id}
                                onClick={() => handleSelect(f.function_id)}
                                style={{
                                    padding: '1rem',
                                    borderBottom: '1px solid #1e293b',
                                    cursor: 'pointer',
                                    background: selectedId === f.function_id ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                                    borderLeft: selectedId === f.function_id ? '3px solid #60a5fa' : '3px solid transparent'
                                }}
                            >
                                <div style={{ fontWeight: 500, color: '#f1f5f9' }}>{f.name}</div>
                                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{f.description || 'No description'}</div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Right Panel: Editor */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: '1.5rem', gap: '1rem' }}>
                {editMode ? (
                    <>
                        {/* Header */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <input
                                type="text"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                style={{ background: 'transparent', border: 'none', fontSize: '1.5rem', fontWeight: 700, color: '#f1f5f9', width: '60%', outline: 'none' }}
                                placeholder="Function Name"
                            />
                            <div style={{ display: 'flex', gap: '1rem' }}>
                                <button
                                    onClick={handleValidate}
                                    style={{
                                        padding: '0.5rem 1rem', background: '#334155', color: '#e2e8f0', border: 'none', borderRadius: '6px',
                                        cursor: 'pointer', display: 'flex', gap: '0.5rem', alignItems: 'center', transition: 'background 0.2s'
                                    }}
                                    className="hover:bg-slate-700"
                                >
                                    <Play size={16} className="text-green-400" /> Dry Run
                                </button>
                                <button
                                    onClick={handleSave}
                                    className="rebuild-btn"
                                    style={{ padding: '0.5rem 1rem', background: '#2563eb', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', display: 'flex', gap: '0.5rem', alignItems: 'center' }}
                                >
                                    <Save size={16} /> Save
                                </button>
                            </div>
                        </div>

                        {/* Description & Config Toggle */}
                        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                            <input
                                type="text"
                                value={description}
                                onChange={e => setDescription(e.target.value)}
                                style={{ flex: 1, background: '#0f172a', border: '1px solid #334155', padding: '0.5rem', borderRadius: '4px', color: '#cbd5e1' }}
                                placeholder="Description (optional)"
                            />
                            <button
                                onClick={() => setShowConfig(!showConfig)}
                                style={{
                                    background: 'transparent', border: 'none', color: showConfig ? '#60a5fa' : '#64748b', cursor: 'pointer',
                                    display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.8rem'
                                }}
                            >
                                <Settings size={16} /> Config
                            </button>
                        </div>

                        {/* Config Section */}
                        {showConfig && (
                            <div style={{
                                background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', padding: '1rem',
                                display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem'
                            }}>
                                <div>
                                    <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                                        Action Space (Comma Sep)
                                    </label>
                                    <input
                                        type="text"
                                        value={actionLabels}
                                        onChange={e => setActionLabels(e.target.value)}
                                        style={{ width: '100%', padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#e2e8f0', fontFamily: 'monospace' }}
                                    />
                                    <div style={{ marginTop: '0.25rem', fontSize: '0.7rem', color: '#64748b' }}>
                                        Exposes: {actionList.map(l => `env.actions.${l.toUpperCase()}`).join(", ")}
                                    </div>
                                </div>
                                <div>
                                    <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.5rem', textTransform: 'uppercase' }}>
                                        Status Space (Comma Sep)
                                    </label>
                                    <input
                                        type="text"
                                        value={statusLabels}
                                        onChange={e => setStatusLabels(e.target.value)}
                                        style={{ width: '100%', padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#e2e8f0', fontFamily: 'monospace' }}
                                    />
                                    <div style={{ marginTop: '0.25rem', fontSize: '0.7rem', color: '#64748b' }}>
                                        Exposes: {statusList.map(l => `env.status.${l.toUpperCase()}`).join(", ")}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Editor Layout: Editor + Schema Sidebar */}
                        <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr 250px', gap: '1rem', minHeight: 0 }}>

                            {/* Editor Area */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                <div style={{ flex: 1, border: '1px solid #334155', borderRadius: '8px', overflow: 'hidden' }}>
                                    <RewardEditor
                                        code={code}
                                        setCode={setCode}
                                        onMount={handleEditorMount}
                                    />
                                </div>

                                {/* Validation Output Console */}
                                {validationResult && (
                                    <div style={{
                                        padding: '1rem', borderRadius: '6px',
                                        background: validationResult.valid ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)',
                                        border: validationResult.valid ? '1px solid #22c55e' : '1px solid #ef4444',
                                        fontSize: '0.9rem', color: '#e2e8f0'
                                    }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 600 }}>
                                            {validationResult.valid ? <CheckCircle size={18} className="text-green-500" /> : <XCircle size={18} className="text-red-500" />}
                                            {validationResult.valid ? "Validation Successful" : "Validation Failed"}
                                        </div>
                                        {validationResult.valid ? (
                                            <div>
                                                Computed Reward: <span style={{ fontFamily: 'monospace', color: '#86efac' }}>{validationResult.result}</span>
                                            </div>
                                        ) : (
                                            <div style={{ fontFamily: 'monospace', color: '#fca5a5' }}>
                                                Error: {validationResult.error}
                                            </div>
                                        )}
                                        {validationResult.valid && validationResult.env_state && (
                                            <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px solid rgba(255,255,255,0.1)', fontSize: '0.8rem', color: '#94a3b8' }}>
                                                Mock Env State: Position={validationResult.env_state.pos}, Unrealized PnL={validationResult.env_state.pnl.toFixed(2)}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Schema Context Sidebar */}
                            <div style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                                {/* Dataset Selector */}
                                <div>
                                    <label style={{ display: 'block', fontSize: '0.75rem', color: '#94a3b8', marginBottom: '0.5rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                                        Reference Dataset
                                    </label>
                                    <select
                                        value={selectedDatasetId}
                                        onChange={e => setSelectedDatasetId(e.target.value)}
                                        style={{ width: '100%', padding: '0.5rem', background: '#1e293b', border: '1px solid #334155', borderRadius: '4px', color: '#e2e8f0', fontSize: '0.9rem' }}
                                    >
                                        <option value="">-- Select Dataset --</option>
                                        {datasets.map(d => (
                                            <option key={d.dataset_id} value={d.dataset_id}>{d.name}</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Environment Variables */}
                                <div>
                                    <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                        <Database size={14} className="text-blue-400" />
                                        Environment State (env)
                                    </div>
                                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                                        {['position', 'entry_price', 'qty', 'balance', 'unrealized_pnl', 'last_reward'].map(v => (
                                            <button
                                                key={v}
                                                onClick={() => insertVariable(`env.${v}`, true)}
                                                className="hover:bg-slate-700 hover:text-white transition-colors"
                                                style={{
                                                    fontSize: '0.75rem', fontFamily: 'monospace',
                                                    color: '#94a3b8', padding: '0.25rem 0.5rem',
                                                    background: '#1e293b', borderRadius: '4px',
                                                    border: '1px solid #334155', cursor: 'pointer'
                                                }}
                                            >
                                                env.{v}
                                            </button>
                                        ))}
                                    </div>
                                    {/* Action Namespace Hints */}
                                    <div style={{ marginTop: '0.5rem', borderTop: '1px solid #334155', paddingTop: '0.5rem' }}>
                                        <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.25rem' }}>Actions</div>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                                            {actionList.map(a => (
                                                <button key={a} onClick={() => insertVariable(`env.actions.${a.toUpperCase()}`, true)}
                                                    style={{ fontSize: '0.7rem', padding: '0.2rem', background: '#0f172a', border: '1px solid #334155', color: '#94a3b8', cursor: 'pointer' }}>
                                                    {a}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div style={{ marginTop: '0.5rem' }}>
                                        <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.25rem' }}>Status</div>
                                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                                            {statusList.map(s => (
                                                <button key={s} onClick={() => insertVariable(`env.status.${s.toUpperCase()}`, true)}
                                                    style={{ fontSize: '0.7rem', padding: '0.2rem', background: '#0f172a', border: '1px solid #334155', color: '#94a3b8', cursor: 'pointer' }}>
                                                    {s}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {/* Dataset Variables */}
                                {selectedDataset ? (
                                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minHeight: 0 }}>
                                        <div style={{ fontSize: '0.8rem', color: '#cbd5e1', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                            <Database size={14} className="text-purple-400" />
                                            Dataset Variables (env.data)
                                        </div>
                                        <div style={{ flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                            {availableColumns.map(col => (
                                                <button
                                                    key={col}
                                                    onClick={() => insertVariable(col)}
                                                    className="hover:bg-slate-700 hover:text-white transition-colors"
                                                    style={{
                                                        fontSize: '0.8rem', fontFamily: 'monospace',
                                                        color: '#94a3b8', padding: '0.4rem 0.5rem',
                                                        background: '#1e293b', borderRadius: '4px',
                                                        border: '1px solid transparent', cursor: 'pointer',
                                                        textAlign: 'left'
                                                    }}
                                                >
                                                    env.data['{col}']
                                                </button>
                                            ))}
                                            {availableColumns.length === 0 && (
                                                <div style={{ fontSize: '0.8rem', color: '#64748b', fontStyle: 'italic' }}>No known columns</div>
                                            )}
                                        </div>
                                    </div>
                                ) : (
                                    <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#64748b', fontSize: '0.8rem', textAlign: 'center' }}>
                                        Select a dataset to see variable hints.
                                    </div>
                                )}
                            </div>
                        </div>
                    </>
                ) : (
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
                        <Code size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                        <p>Select a function to edit or create a new one.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MlRewardFunctions;
