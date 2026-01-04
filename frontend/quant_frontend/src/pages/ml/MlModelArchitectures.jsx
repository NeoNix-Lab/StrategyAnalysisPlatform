import React, { useState, useEffect } from 'react';
import { Plus, Save, Layers, Settings, Database, Trash2 } from 'lucide-react';
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
                setEditMode(false);
                setSelectedId(null);
            } else {
                alert("Failed to save model");
            }
        } catch (e) { console.error(e); }
    };

    const cardClass = "bg-bg-secondary/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl flex flex-col overflow-hidden";

    return (
        <div className="grid grid-cols-[250px_1fr] gap-8 h-[calc(100vh-140px)]">

            {/* List Panel */}
            <div className={`${cardClass} p-0`}>
                <div className="p-4 border-b border-slate-700/50 flex justify-between items-center bg-bg-secondary/30">
                    <h3 className="m-0 text-base font-semibold text-text-primary">Architectures</h3>
                    <button onClick={handleCreateNew} className="bg-transparent border-none text-sky-400 cursor-pointer hover:text-sky-300 transition-colors">
                        <Plus size={18} />
                    </button>
                </div>
                <div className="overflow-y-auto flex-1 custom-scrollbar">
                    {loading && !selectedId ? (
                        <div className="p-4 text-text-muted">Loading...</div>
                    ) : (
                        models.map(m => (
                            <div
                                key={m.model_id}
                                onClick={() => handleSelect(m.model_id)}
                                className={`p-4 border-b border-slate-800/50 cursor-pointer transition-all border-l-[3px]
                                ${selectedId === m.model_id
                                        ? 'bg-violet-500/10 border-l-violet-400'
                                        : 'bg-transparent border-l-transparent hover:bg-white/5'
                                    }`}
                            >
                                <div className="font-medium text-slate-100">{m.name}</div>
                                <div className="text-xs text-text-muted mt-1 truncate">{m.description || 'No description'}</div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Editor Panel */}
            <div className={`${cardClass} p-6 gap-4`}>
                {editMode ? (
                    <>
                        <div className="flex justify-between items-center gap-4">
                            <input
                                type="text"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                className="bg-transparent border-none text-2xl font-bold text-text-primary w-full outline-none placeholder:text-slate-600 focus:placeholder:text-slate-500"
                                placeholder="Model Name"
                            />
                            <button
                                onClick={handleSave}
                                className="px-4 py-2 bg-blue-600 text-white border-none rounded-lg cursor-pointer flex gap-2 items-center hover:bg-blue-500 transition-colors font-medium text-sm whitespace-nowrap shadow-lg shadow-blue-900/20"
                            >
                                <Save size={16} /> Save
                            </button>
                        </div>
                        <input
                            type="text"
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            className="bg-slate-900/50 border border-slate-700 rounded-lg p-2 text-slate-300 outline-none focus:border-blue-500 transition-colors"
                            placeholder="Description (optional)"
                        />
                        <div className="flex-1 overflow-y-auto border border-slate-700/50 rounded-xl p-4 bg-slate-900/30 custom-scrollbar">
                            <ModelBuilder layers={layers} setLayers={setLayers} />
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-text-secondary select-none">
                        <Layers size={48} className="opacity-20 mb-4" />
                        <p className="text-sm">Select a model to edit or create a new one.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MlModelArchitectures;
