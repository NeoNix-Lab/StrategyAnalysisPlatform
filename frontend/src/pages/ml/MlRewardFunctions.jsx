import React, { useState, useEffect } from 'react';
import { Plus, Save, Trash2, Code } from 'lucide-react';
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

    const DEFAULT_CODE = `def calculate_reward(env, action):
    # Available: env.last_reward, env.data, etc.
    reward = env.last_reward
    if reward < 0:
        reward *= 1.1 # Penalty
    return reward
`;

    useEffect(() => {
        fetchFunctions();
    }, []);

    const fetchFunctions = async () => {
        try {
            const res = await fetch('/api/ml/studio/functions');
            if (res.ok) setFunctions(await res.json());
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
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
                setEditMode(true); // Auto switch to edit/view mode
            }
        } finally { setLoading(false); }
    };

    const handleCreateNew = () => {
        setSelectedId(null);
        setName('New Reward Function');
        setCode(DEFAULT_CODE);
        setDescription('');
        setEditMode(true);
    };

    const handleSave = async () => {
        const payload = { name, code, description };
        // Determine URL and Method based on whether we are updating (not supported yet fully API-wise usually but let's assume POST for new) 
        // NOTE: The API only supports Create (POST) for now based on previous context. Updating might create duplicates or need PUT.
        // For now, I'll treat everything as CREATE NEW if no ID, but since API is append-only for now, I'll just use POST.

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

    return (
        <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '2rem', height: 'calc(100vh - 140px)' }}>

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
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <input
                                type="text"
                                value={name}
                                onChange={e => setName(e.target.value)}
                                style={{ background: 'transparent', border: 'none', fontSize: '1.5rem', fontWeight: 700, color: '#f1f5f9', width: '100%', outline: 'none' }}
                                placeholder="Function Name"
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
                        <div style={{ flex: 1, border: '1px solid #334155', borderRadius: '8px', overflow: 'hidden' }}>
                            <RewardEditor code={code} setCode={setCode} />
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
