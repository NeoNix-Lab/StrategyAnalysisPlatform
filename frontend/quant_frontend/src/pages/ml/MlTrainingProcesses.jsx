import React, { useState, useEffect } from 'react';
import { Plus, Save, Zap, Settings, Trash2 } from 'lucide-react';
import ProcessConfig from './components/ProcessConfig';
import api from '../../api/axios';

const MlTrainingProcesses = () => {
    const [processes, setProcesses] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [editMode, setEditMode] = useState(false);
    const [loading, setLoading] = useState(true);

    const [name, setName] = useState('');
    const [config, setConfig] = useState({
        epochs: 10,
        batch_size: 32,
        learning_rate: 0.001,
        epsilon_start: 1.0,
        epsilon_end: 0.01,
        epsilon_decay: 0.995,
        window_size: 20
    });
    const [description, setDescription] = useState('');

    useEffect(() => {
        fetchProcesses();
    }, []);

    const fetchProcesses = async () => {
        try {
            const res = await api.get('/ml/studio/processes');
            setProcesses(res.data);
        } catch (e) { console.error(e); }
        finally { setLoading(false); }
    };

    const handleSelect = async (id) => {
        setLoading(true);
        try {
            const res = await api.get(`/ml/studio/processes/${id}`);
            const data = res.data;
            setSelectedId(id);
            setName(data.name);
            // Extract only config fields
            const { process_id, name, description, ...rest } = data;
            setConfig(rest);
            setDescription(description || '');
            setEditMode(true);
        } finally { setLoading(false); }
    };

    const handleCreateNew = () => {
        setSelectedId(null);
        setName('New Process Config');
        setConfig({
            epochs: 10,
            batch_size: 32,
            learning_rate: 0.001,
            epsilon_start: 1.0,
            epsilon_end: 0.01,
            epsilon_decay: 0.995,
            window_size: 20
        });
        setDescription('');
        setEditMode(true);
    };

    const handleSave = async () => {
        const payload = { name, ...config, description };
        try {
            await api.post('/ml/studio/processes', payload);
            await fetchProcesses();
            setEditMode(false);
            setSelectedId(null);
        } catch (e) {
            console.error(e);
            alert("Failed to save process");
        }
    };

    const cardClass = "bg-bg-secondary/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl flex flex-col overflow-hidden";

    return (
        <div className="grid grid-cols-[250px_1fr] gap-8 h-[calc(100vh-140px)]">

            {/* List Panel */}
            <div className={`${cardClass} p-0`}>
                <div className="p-4 border-b border-slate-700/50 flex justify-between items-center bg-bg-secondary/30">
                    <h3 className="m-0 text-base font-semibold text-text-primary">Configs</h3>
                    <button onClick={handleCreateNew} className="bg-transparent border-none text-sky-400 cursor-pointer hover:text-sky-300 transition-colors">
                        <Plus size={18} />
                    </button>
                </div>
                <div className="overflow-y-auto flex-1 custom-scrollbar">
                    {loading && !selectedId ? (
                        <div className="p-4 text-text-muted">Loading...</div>
                    ) : (
                        processes.map(p => (
                            <div
                                key={p.process_id}
                                onClick={() => handleSelect(p.process_id)}
                                className={`p-4 border-b border-slate-800/50 cursor-pointer transition-all border-l-[3px]
                                ${selectedId === p.process_id
                                        ? 'bg-violet-500/10 border-l-violet-400'
                                        : 'bg-transparent border-l-transparent hover:bg-white/5'
                                    }`}
                            >
                                <div className="font-medium text-slate-100">{p.name}</div>
                                <div className="text-xs text-text-muted mt-1">Epochs: {p.epochs}</div>
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
                                placeholder="Config Name"
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
                            <ProcessConfig config={config} setConfig={setConfig} />
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-text-secondary select-none">
                        <Zap size={48} className="opacity-20 mb-4" />
                        <p className="text-sm">Select a configuration to edit or create a new one.</p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default MlTrainingProcesses;
