import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Brain, Layers, Zap, ArrowRight, ExternalLink, Database } from 'lucide-react';
import '../Dashboard.css';

const MlCompose = () => {
    const navigate = useNavigate();
    const [functions, setFunctions] = useState([]);
    const [models, setModels] = useState([]);
    const [processes, setProcesses] = useState([]);
    const [datasets, setDatasets] = useState([]);

    const [sessionName, setSessionName] = useState('');
    const [selectedFunction, setSelectedFunction] = useState('');
    const [selectedModel, setSelectedModel] = useState('');
    const [selectedProcess, setSelectedProcess] = useState('');
    const [selectedDataset, setSelectedDataset] = useState('');

    useEffect(() => {
        // Load all options
        Promise.all([
            fetch('/api/ml/studio/functions').then(res => res.json()),
            fetch('/api/ml/studio/models').then(res => res.json()),
            fetch('/api/ml/studio/processes').then(res => res.json()),
            fetch('/api/datasets').then(res => res.json())
        ]).then(([f, m, p, d]) => {
            setFunctions(f);
            setModels(m);
            setProcesses(p);
            setDatasets(d);
        }).catch(console.error);
    }, []);

    const handleCreate = async () => {
        if (!sessionName || !selectedFunction || !selectedModel || !selectedProcess || !selectedDataset) return;

        try {
            // 1. Create Session
            const sessRes = await fetch('/api/ml/studio/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: sessionName,
                    function_id: selectedFunction,
                    model_id: selectedModel,
                    process_id: selectedProcess
                })
            });

            if (sessRes.ok) {
                const sessData = await sessRes.json();

                // 2. Create Initial Iteration (Bind Dataset)
                const iterRes = await fetch('/api/ml/studio/iterations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        session_id: sessData.session_id,
                        dataset_id: selectedDataset,
                        name: 'Initial Run',
                        split_config: { train: 0.7, test: 0.2, work: 0.1 }
                    })
                });

                if (iterRes.ok) {
                    const iterData = await iterRes.json();
                    navigate(`/ml/studio/session/${sessData.session_id}/run/${iterData.iteration_id}`);
                } else {
                    alert("Session created, but failed to create initial iteration.");
                    navigate(`/ml/studio/session/${sessData.session_id}`);
                }
            } else {
                alert("Failed to create session");
            }
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="dashboard-container" style={{ padding: '0', maxWidth: '1000px', margin: '0 auto' }}>
            <div className="card" style={{ marginTop: '2rem', padding: '2rem' }}>
                <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
                    <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>Compose New Experiment</h2>
                    <p style={{ color: '#94a3b8' }}>Assemble your strategy blueprint and bind it to a dataset.</p>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem' }}>
                    {/* Session Name */}
                    <div>
                        <label style={{ display: 'block', marginBottom: '0.5rem', color: '#cbd5e1' }}>Experiment Name</label>
                        <input
                            type="text"
                            className="bg-slate-900 border border-slate-700 rounded p-3 text-white w-full focus:ring-2 focus:ring-blue-500 outline-none"
                            placeholder="e.g. BTC Breakout V1"
                            value={sessionName}
                            onChange={e => setSessionName(e.target.value)}
                        />
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
                        {/* Row 1: Dataset & Reward */}
                        <SelectionBox
                            title="Target Dataset"
                            icon={Database}
                            options={datasets}
                            value={selectedDataset}
                            onChange={setSelectedDataset}
                            linkTo="/datasets"
                            idKey="dataset_id"
                        />
                        <SelectionBox
                            title="Reward Function"
                            icon={Brain}
                            options={functions}
                            value={selectedFunction}
                            onChange={setSelectedFunction}
                            linkTo="/ml/studio/rewards"
                            idKey="function_id"
                        />

                        {/* Row 2: Model & Process */}
                        <SelectionBox
                            title="Model Architecture"
                            icon={Layers}
                            options={models}
                            value={selectedModel}
                            onChange={setSelectedModel}
                            linkTo="/ml/studio/models"
                            idKey="model_id"
                        />
                        <SelectionBox
                            title="Training Config"
                            icon={Zap}
                            options={processes}
                            value={selectedProcess}
                            onChange={setSelectedProcess}
                            linkTo="/ml/studio/processes"
                            idKey="process_id"
                        />
                    </div>

                    <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '2rem', paddingTop: '2rem', borderTop: '1px solid #334155' }}>
                        <button
                            onClick={handleCreate}
                            disabled={!sessionName || !selectedFunction || !selectedModel || !selectedProcess || !selectedDataset}
                            style={{
                                background: 'linear-gradient(135deg, #4f46e5, #3b82f6)',
                                color: 'white',
                                padding: '0.75rem 2rem',
                                borderRadius: '8px',
                                border: 'none',
                                fontWeight: 600,
                                cursor: 'pointer',
                                opacity: (!sessionName || !selectedFunction || !selectedModel || !selectedProcess || !selectedDataset) ? 0.5 : 1,
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}
                        >
                            <Play size={18} /> Launch Experiment
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const SelectionBox = ({ title, icon: Icon, options, value, onChange, linkTo, idKey }) => (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: '#cbd5e1', fontWeight: 500 }}>
                <Icon size={16} color="#94a3b8" /> {title}
            </label>
            <a href={linkTo} style={{ fontSize: '0.75rem', color: '#60a5fa', textDecoration: 'none', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                Manage <ExternalLink size={10} />
            </a>
        </div>
        <select
            value={value}
            onChange={e => onChange(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded p-3 text-slate-200 w-full focus:ring-2 focus:ring-blue-500 outline-none appearance-none"
            style={{ backgroundImage: 'none' }} // Remove default arrow if customized
        >
            <option value="">Select...</option>
            {options && Array.isArray(options) && options.map(opt => (
                <option key={opt[idKey]} value={opt[idKey]}>{opt.name}</option>
            ))}
        </select>
        {value && <div style={{ fontSize: '0.75rem', color: '#64748b' }}>selected ID: {value.substring(0, 8)}...</div>}
    </div>
);

export default MlCompose;
