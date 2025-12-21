import React, { useState, useEffect } from 'react';
import { Plus, Save, Layers } from 'lucide-react';
import ModelBuilder from './components/ModelBuilder';
import '../Dashboard.css';

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

    return (
        <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '2rem', height: 'calc(100vh - 140px)' }}>

            {/* List Panel */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: '0', overflow: 'hidden' }}>
                <div style={{ padding: '1rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ margin: 0, fontSize: '1rem' }}>Architectures</h3>
                    <button onClick={handleCreateNew} style={{ background: 'transparent', border: 'none', color: '#60a5fa', cursor: 'pointer' }}>
                        <Plus size={18} />
                    </button>
                </div>
                <div style={{ overflowY: 'auto', flex: 1 }}>
                    {loading && !selectedId ? (
                        <div style={{ padding: '1rem', color: '#64748b' }}>Loading...</div>
                    ) : (
                        models.map(m => (
                            <div
                                key={m.model_id}
                                onClick={() => handleSelect(m.model_id)}
                                style={{
                                    padding: '1rem',
                                    borderBottom: '1px solid #1e293b',
                                    cursor: 'pointer',
                                    background: selectedId === m.model_id ? 'rgba(59, 130, 246, 0.1)' : 'transparent',
                                    borderLeft: selectedId === m.model_id ? '3px solid #60a5fa' : '3px solid transparent'
                                }}
                            >
                                <div style={{ fontWeight: 500, color: '#f1f5f9' }}>{m.name}</div>
                                <div style={{ fontSize: '0.75rem', color: '#64748b' }}>{m.description || 'No description'}</div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* Editor Panel */}
            <div className="card" style={{ display: 'flex', flexDirection: 'column', padding: '1.5rem', gap: '1rem' }}>
                {editMode ? (
                    <>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <input
                                type="text"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                style={{ background: 'transparent', border: 'none', fontSize: '1.5rem', fontWeight: 700, color: '#f1f5f9', width: '100%', outline: 'none' }}
                                placeholder="Model Name"
                            />
                            <button
                                onClick={handleSave}
                                className="rebuild-btn"
                                style={{ padding: '0.5rem 1rem', background: '#2563eb', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', display: 'flex', gap: '0.5rem', alignItems: 'center' }}
                            >
                                <Save size={16} /> Save
                            </button>
                        </div>
                        <input
                            type="text"
                            value={description}
                            onChange={e => setDescription(e.target.value)}
                            style={{ background: '#0f172a', border: '1px solid #334155', padding: '0.5rem', borderRadius: '4px', color: '#cbd5e1' }}
                            placeholder="Description (optional)"
                        />
                        <div style={{ flex: 1, overflowY: 'auto' }}>
                            <ModelBuilder layers={layers} setLayers={setLayers} />
                        </div>
                    </>
                ) : (
                    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
                        <Layers size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                        <p>Select a model to edit or create a new one.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MlModelArchitectures;
