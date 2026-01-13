import React, { useState, useEffect } from 'react';
import { Plus, Save, Layers, Settings, Database, Trash2, ArrowLeft, ChevronRight } from 'lucide-react';
import ModelBuilder from './components/ModelBuilder';

const MlModelArchitectures = () => {
    const [models, setModels] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [editMode, setEditMode] = useState(false);
    const [loading, setLoading] = useState(true);

    const [name, setName] = useState('');
    const [layers, setLayers] = useState([]);
    const [description, setDescription] = useState('');

    const DEFAULT_LAYERS = [
        { type: 'Dense', units: 64, activation: 'relu' },
        { type: 'Dense', units: 32, activation: 'relu' },
        { type: 'Dense', units: 3, activation: 'linear' }
    ];

    useEffect(() => {
        fetchModels();
    }, []);

    const fetchModels = async () => {
        try {
            const res = await fetch('/api/ml/studio/models');
            if (res.ok) setModels(await res.json());
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const handleSelect = async (id) => {
        setLoading(true);
        try {
            const res = await fetch(`/api/ml/studio/models/${id}`);
            if (res.ok) {
                const data = await res.json();
                setSelectedId(id);
                setName(data.name);
                setLayers(data.layers_json);
                setDescription(data.description || '');
                setEditMode(true);
            }
        } finally { setLoading(false); }
    };

    const handleCreateNew = () => {
        setSelectedId(null);
        setName('New Architecture');
        setLayers(DEFAULT_LAYERS);
        setDescription('');
        setEditMode(true);
    };

    const handleSave = async () => {
        const payload = { name, layers_json: layers, description };
        try {
            const res = await fetch('/api/ml/studio/models', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                await fetchModels();
                // Keep editing
            } else {
                alert("Failed to save model");
            }
        } catch (e) { console.error(e); }
    };

    return (
        <div className="flex h-[calc(100vh-60px)] -m-8">
            {/* List Sidebar */}
            <div className="w-[300px] flex-none border-r border-slate-800 bg-slate-900/50 flex flex-col">
                <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-900/80 backdrop-blur-sm">
                    <h3 className="m-0 text-sm font-bold text-slate-300 uppercase tracking-wider">Models</h3>
                    <button onClick={handleCreateNew} className="p-2 rounded-lg bg-blue-600/10 text-blue-400 hover:bg-blue-600 hover:text-white transition-all">
                        <Plus size={16} />
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar p-2">
                    {loading && !selectedId ? (
                        <div className="p-8 text-center text-slate-500 text-sm">Loading architectures...</div>
                    ) : (
                        models.map(m => (
                            <div
                                key={m.model_id}
                                onClick={() => handleSelect(m.model_id)}
                                className={`p-4 mb-2 rounded-xl cursor-pointer transition-all border group relative overflow-hidden
                                ${selectedId === m.model_id
                                        ? 'bg-violet-600/10 border-violet-500/50'
                                        : 'bg-transparent border-transparent hover:bg-slate-800/50'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-1">
                                    <div className={`font-semibold text-sm ${selectedId === m.model_id ? 'text-violet-200' : 'text-slate-300 group-hover:text-slate-200'}`}>
                                        {m.name}
                                    </div>
                                    {selectedId === m.model_id && <ChevronRight size={16} className="text-violet-500" />}
                                </div>
                                <div className="text-xs text-slate-500 truncate">{m.description || 'No description'}</div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Main Workspace */}
            <div className="flex-1 flex flex-col bg-[#020617] relative overflow-hidden">
                {/* Background Pattern */}
                <div className="absolute inset-0 bg-[linear-gradient(rgba(30,41,59,0.3)_1px,transparent_1px),linear-gradient(90deg,rgba(30,41,59,0.3)_1px,transparent_1px)] [background-size:40px_40px] opacity-20 pointer-events-none"></div>

                {editMode ? (
                    <>
                        {/* Workspace Header / Chrome */}
                        <div className="h-20 px-8 flex items-center justify-between border-b border-slate-800/50 bg-slate-900/30 backdrop-blur-sm relative z-20">
                            <div className="flex-1 max-w-2xl flex flex-col gap-1">
                                <input
                                    type="text"
                                    value={name}
                                    onChange={e => setName(e.target.value)}
                                    className="bg-transparent border-none text-xl font-bold text-slate-100 placeholder:text-slate-600 focus:outline-none w-full"
                                    placeholder="Model Name"
                                />
                                <input
                                    type="text"
                                    value={description}
                                    onChange={e => setDescription(e.target.value)}
                                    className="bg-transparent border-none text-sm text-slate-400 placeholder:text-slate-600 focus:outline-none w-full"
                                    placeholder="Add a brief description..."
                                />
                            </div>

                            <div className="flex items-center gap-4">
                                <div className="text-xs font-mono text-slate-500 px-3 py-1 bg-slate-900 rounded border border-slate-800">
                                    {layers.length} Layers
                                </div>
                                <button
                                    onClick={handleSave}
                                    className="px-6 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-500 transition-all font-medium text-sm shadow-lg shadow-violet-900/20 flex items-center gap-2"
                                >
                                    <Save size={16} /> Save Changes
                                </button>
                            </div>
                        </div>

                        {/* Builder Canvas */}
                        <div className="flex-1 overflow-hidden p-6 relative z-10">
                            <ModelBuilder layers={layers} setLayers={setLayers} />
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-slate-600 select-none z-10">
                        <div className="w-24 h-24 rounded-full bg-slate-900/50 flex items-center justify-center mb-6 border border-slate-800">
                            <Layers size={48} className="opacity-40" />
                        </div>
                        <h2 className="text-xl font-semibold text-slate-300 mb-2">Select a Model</h2>
                        <p className="text-sm max-w-sm text-center">Choose an architecture from the sidebar or create a new one to start building.</p>
                        <button onClick={handleCreateNew} className="mt-8 px-6 py-3 bg-slate-800 text-slate-300 rounded-lg border border-slate-700 hover:bg-slate-700 transition-all flex items-center gap-2">
                            <Plus size={18} /> Create New Architecture
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MlModelArchitectures;
