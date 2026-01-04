import React, { useState, useEffect, useRef } from 'react';
import { Plus, Save, Trash2, Code, Play, CheckCircle, XCircle, Database, Settings } from 'lucide-react';
import RewardEditor from './components/RewardEditor';

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

    const cardClass = "bg-bg-secondary/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl flex flex-col overflow-hidden";

    return (
        <div className="grid grid-cols-[250px_1fr] gap-8 h-[calc(100vh-140px)]">

            {/* Left Panel: List */}
            <div className={`${cardClass} p-0`}>
                <div className="p-4 border-b border-slate-700/50 flex justify-between items-center bg-bg-secondary/30">
                    <h3 className="m-0 text-base font-semibold text-text-primary">Functions</h3>
                    <button onClick={handleCreateNew} className="bg-transparent border-none text-sky-400 cursor-pointer hover:text-sky-300 transition-colors">
                        <Plus size={18} />
                    </button>
                </div>
                <div className="overflow-y-auto flex-1 custom-scrollbar">
                    {loading && !selectedId ? (
                        <div className="p-4 text-text-muted">Loading...</div>
                    ) : (
                        functions.map(f => (
                            <div
                                key={f.function_id}
                                onClick={() => handleSelect(f.function_id)}
                                className={`p-4 border-b border-slate-800/50 cursor-pointer transition-all border-l-[3px]
                                ${selectedId === f.function_id
                                        ? 'bg-violet-500/10 border-l-violet-400'
                                        : 'bg-transparent border-l-transparent hover:bg-white/5'
                                    }`}
                            >
                                <div className="font-medium text-slate-100">{f.name}</div>
                                <div className="text-xs text-text-muted mt-1 truncate">{f.description || 'No description'}</div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Right Panel: Editor */}
            <div className={`${cardClass} p-6 gap-4`}>
                {editMode ? (
                    <>
                        {/* Header */}
                        <div className="flex justify-between items-center gap-4">
                            <input
                                type="text"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                className="bg-transparent border-none text-2xl font-bold text-text-primary w-full outline-none placeholder:text-slate-600 focus:placeholder:text-slate-500"
                                placeholder="Function Name"
                            />
                            <div className="flex gap-4">
                                <button
                                    onClick={handleValidate}
                                    className="px-4 py-2 bg-slate-700 text-slate-200 border-none rounded-lg cursor-pointer flex gap-2 items-center hover:bg-slate-600 transition-colors font-medium text-sm"
                                >
                                    <Play size={16} className="text-green-400" /> Dry Run
                                </button>
                                <button
                                    onClick={handleSave}
                                    className="px-4 py-2 bg-blue-600 text-white border-none rounded-lg cursor-pointer flex gap-2 items-center hover:bg-blue-500 transition-colors font-medium text-sm whitespace-nowrap shadow-lg shadow-blue-900/20"
                                >
                                    <Save size={16} /> Save
                                </button>
                            </div>
                        </div>

                        {/* Description & Config Toggle */}
                        <div className="flex gap-4 items-center">
                            <input
                                type="text"
                                value={description}
                                onChange={e => setDescription(e.target.value)}
                                className="flex-1 bg-slate-900/50 border border-slate-700/50 rounded-lg p-2 text-slate-300 outline-none focus:border-blue-500 transition-colors"
                                placeholder="Description (optional)"
                            />
                            <button
                                onClick={() => setShowConfig(!showConfig)}
                                className={`bg-transparent border-none cursor-pointer flex items-center gap-1 text-sm font-medium transition-colors
                                ${showConfig ? 'text-blue-400' : 'text-slate-400 hover:text-slate-300'}`}
                            >
                                <Settings size={16} /> Config
                            </button>
                        </div>

                        {/* Config Section */}
                        {showConfig && (
                            <div className="bg-slate-900/50 border border-slate-700/50 rounded-xl p-4 grid grid-cols-2 gap-4 animate-fade-in">
                                <div>
                                    <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                                        Action Space (Comma Sep)
                                    </label>
                                    <input
                                        type="text"
                                        value={actionLabels}
                                        onChange={e => setActionLabels(e.target.value)}
                                        className="w-full p-2 bg-slate-800 border border-slate-600 rounded text-slate-200 font-mono text-xs focus:ring-1 focus:ring-blue-500 outline-none"
                                    />
                                    <div className="mt-1 text-[10px] text-slate-500 font-mono truncate">
                                        Exposes: {actionList.map(l => `env.actions.${l.toUpperCase()}`).join(", ")}
                                    </div>
                                </div>
                                <div>
                                    <label className="block text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                                        Status Space (Comma Sep)
                                    </label>
                                    <input
                                        type="text"
                                        value={statusLabels}
                                        onChange={e => setStatusLabels(e.target.value)}
                                        className="w-full p-2 bg-slate-800 border border-slate-600 rounded text-slate-200 font-mono text-xs focus:ring-1 focus:ring-blue-500 outline-none"
                                    />
                                    <div className="mt-1 text-[10px] text-slate-500 font-mono truncate">
                                        Exposes: {statusList.map(l => `env.status.${l.toUpperCase()}`).join(", ")}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Editor Layout: Editor + Schema Sidebar */}
                        <div className="flex-1 grid grid-cols-[1fr_250px] gap-4 min-h-0">

                            {/* Editor Area */}
                            <div className="flex flex-col gap-4">
                                <div className="flex-1 border border-slate-700/50 rounded-lg overflow-hidden bg-[#1e1e1e]">
                                    <RewardEditor
                                        code={code}
                                        setCode={setCode}
                                        onMount={handleEditorMount}
                                    />
                                </div>

                                {/* Validation Output Console */}
                                {validationResult && (
                                    <div className={`p-4 rounded-lg border text-sm animate-fade-in
                                    ${validationResult.valid
                                            ? 'bg-green-500/10 border-green-500/50 text-slate-200'
                                            : 'bg-red-500/10 border-red-500/50 text-slate-200'}`}>
                                        <div className="flex items-center gap-2 mb-2 font-semibold">
                                            {validationResult.valid ? <CheckCircle size={18} className="text-green-500" /> : <XCircle size={18} className="text-red-500" />}
                                            {validationResult.valid ? "Validation Successful" : "Validation Failed"}
                                        </div>
                                        {validationResult.valid ? (
                                            <div>
                                                Computed Reward: <span className="font-mono text-green-300">{validationResult.result}</span>
                                            </div>
                                        ) : (
                                            <div className="font-mono text-red-300">
                                                Error: {validationResult.error}
                                            </div>
                                        )}
                                        {validationResult.valid && validationResult.env_state && (
                                            <div className="mt-2 pt-2 border-t border-white/10 text-xs text-slate-400 font-mono">
                                                Mock Env State: Position={validationResult.env_state.pos}, Unrealized PnL={validationResult.env_state.pnl.toFixed(2)}
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* Schema Context Sidebar */}
                            <div className="bg-slate-900/30 border border-slate-700/50 rounded-xl p-4 flex flex-col gap-4 overflow-y-auto custom-scrollbar">
                                {/* Dataset Selector */}
                                <div>
                                    <label className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                                        Reference Dataset
                                    </label>
                                    <select
                                        value={selectedDatasetId}
                                        onChange={e => setSelectedDatasetId(e.target.value)}
                                        className="w-full p-2 bg-slate-800 border border-slate-600 rounded text-slate-200 text-xs focus:ring-1 focus:ring-blue-500 outline-none"
                                    >
                                        <option value="">-- Select Dataset --</option>
                                        {datasets.map(d => (
                                            <option key={d.dataset_id} value={d.dataset_id}>{d.name}</option>
                                        ))}
                                    </select>
                                </div>

                                {/* Environment Variables */}
                                <div>
                                    <div className="text-xs text-slate-300 mb-2 flex items-center gap-2 font-medium">
                                        <Database size={14} className="text-blue-400" />
                                        Environment State (env)
                                    </div>
                                    <div className="flex flex-wrap gap-1.5">
                                        {['position', 'entry_price', 'qty', 'balance', 'unrealized_pnl', 'last_reward'].map(v => (
                                            <button
                                                key={v}
                                                onClick={() => insertVariable(`env.${v}`, true)}
                                                className="px-2 py-1 bg-slate-800 border border-slate-700 rounded text-[10px] font-mono text-slate-400 hover:bg-slate-700 hover:text-white transition-colors cursor-pointer"
                                            >
                                                env.{v}
                                            </button>
                                        ))}
                                    </div>
                                    {/* Action Namespace Hints */}
                                    <div className="mt-3 pt-2 border-t border-slate-800">
                                        <div className="text-[10px] text-slate-400 mb-1">Actions</div>
                                        <div className="flex flex-wrap gap-1.5">
                                            {actionList.map(a => (
                                                <button key={a} onClick={() => insertVariable(`env.actions.${a.toUpperCase()}`, true)}
                                                    className="px-1.5 py-0.5 bg-slate-900 border border-slate-800 rounded text-[10px] text-slate-500 hover:text-slate-300 transition-colors">
                                                    {a}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                    <div className="mt-2">
                                        <div className="text-[10px] text-slate-400 mb-1">Status</div>
                                        <div className="flex flex-wrap gap-1.5">
                                            {statusList.map(s => (
                                                <button key={s} onClick={() => insertVariable(`env.status.${s.toUpperCase()}`, true)}
                                                    className="px-1.5 py-0.5 bg-slate-900 border border-slate-800 rounded text-[10px] text-slate-500 hover:text-slate-300 transition-colors">
                                                    {s}
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {/* Dataset Variables */}
                                {selectedDataset ? (
                                    <div className="flex-1 flex flex-col min-h-0">
                                        <div className="text-xs text-slate-300 mb-2 flex items-center gap-2 font-medium">
                                            <Database size={14} className="text-purple-400" />
                                            Dataset Variables (env.data)
                                        </div>
                                        <div className="flex-1 overflow-y-auto flex flex-col gap-1 pr-1 custom-scrollbar">
                                            {availableColumns.map(col => (
                                                <button
                                                    key={col}
                                                    onClick={() => insertVariable(col)}
                                                    className="px-2 py-1.5 bg-slate-800 border border-transparent hover:border-slate-600 rounded text-xs font-mono text-slate-400 hover:bg-slate-700 hover:text-white transition-all cursor-pointer text-left truncate"
                                                >
                                                    env.data['{col}']
                                                </button>
                                            ))}
                                            {availableColumns.length === 0 && (
                                                <div className="text-xs text-slate-600 italic p-2">No known columns</div>
                                            )}
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex-1 flex items-center justify-center text-slate-600 text-xs text-center p-4 border border-dashed border-slate-800 rounded-lg">
                                        Select a dataset to see variable hints.
                                    </div>
                                )}
                            </div>
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-text-secondary select-none">
                        <Code size={48} className="opacity-20 mb-4" />
                        <p className="text-sm">Select a function to edit or create a new one.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MlRewardFunctions;
