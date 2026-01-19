import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Play, Brain, Layers, Zap, ArrowRight, ExternalLink, Database } from 'lucide-react';
import api from '../../api/axios';

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
            api.get('/ml/studio/functions').then(res => res.data),
            api.get('/ml/studio/models').then(res => res.data),
            api.get('/ml/studio/processes').then(res => res.data),
            api.get('/datasets').then(res => res.data)
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
            const sessRes = await api.post('/ml/studio/sessions', {
                name: sessionName,
                function_id: selectedFunction,
                model_id: selectedModel,
                process_id: selectedProcess
            });

            const sessData = sessRes.data;

            // 2. Create Initial Iteration (Bind Dataset)
            const iterRes = await api.post('/ml/studio/iterations', {
                session_id: sessData.session_id,
                dataset_id: selectedDataset,
                name: 'Initial Run',
                split_config: { train: 0.7, test: 0.2, work: 0.1 }
            });

            const iterData = iterRes.data;
            navigate(`/ml/studio/session/${sessData.session_id}/run/${iterData.iteration_id}`);
        } catch (e) {
            alert("Session created, but failed to create initial iteration (or session failed).");
            console.error(e);
        }

    };

    return (
        <div className="max-w-[1000px] mx-auto animate-fade-in p-6">
            <div className="bg-bg-secondary/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-8 shadow-2xl relative overflow-hidden">
                <div className="absolute top-0 right-0 p-32 bg-violet-500/10 blur-[100px] rounded-full -mr-16 -mt-16 pointer-events-none"></div>
                <div className="mb-8 text-center relative z-10">
                    <h2 className="text-3xl font-bold text-text-primary mb-2 bg-clip-text text-transparent bg-gradient-to-r from-violet-400 to-sky-400">Compose New Experiment</h2>
                    <p className="text-text-secondary">Assemble your strategy blueprint and bind it to a dataset.</p>
                </div>

                <div className="flex flex-col gap-8 relative z-10">
                    {/* Session Name */}
                    <div>
                        <label className="block mb-2 text-slate-300 font-medium">Experiment Name</label>
                        <input
                            type="text"
                            className="bg-slate-900/50 border border-slate-700/50 rounded-lg p-4 text-white w-full focus:ring-2 focus:ring-violet-500/50 focus:border-violet-500 outline-none transition-all placeholder:text-slate-600 font-medium text-lg"
                            placeholder="e.g. BTC Breakout V1"
                            value={sessionName}
                            onChange={e => setSessionName(e.target.value)}
                        />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
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

                    <div className="flex justify-end mt-8 pt-8 border-t border-slate-700/50">
                        <button
                            onClick={handleCreate}
                            disabled={!sessionName || !selectedFunction || !selectedModel || !selectedProcess || !selectedDataset}
                            className={`
                                flex items-center gap-2 px-8 py-3 rounded-xl font-bold text-white transition-all shadow-lg
                                ${(!sessionName || !selectedFunction || !selectedModel || !selectedProcess || !selectedDataset)
                                    ? 'bg-slate-700 text-slate-400 cursor-not-allowed shadow-none'
                                    : 'bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 shadow-violet-900/30 hover:shadow-violet-900/50 transform hover:-translate-y-0.5'}
                            `}
                        >
                            <Play size={18} fill="currentColor" /> Launch Experiment
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const SelectionBox = ({ title, icon: Icon, options, value, onChange, linkTo, idKey }) => (
    <div className="flex flex-col gap-2 group">
        <div className="flex justify-between items-center">
            <label className="flex items-center gap-2 text-slate-300 font-medium group-focus-within:text-violet-400 transition-colors">
                <Icon size={18} className="text-slate-500 group-focus-within:text-violet-400 transition-colors" /> {title}
            </label>
            <a href={linkTo} className="text-xs text-sky-500 hover:text-sky-400 flex items-center gap-1 transition-colors">
                Manage <ExternalLink size={10} />
            </a>
        </div>
        <select
            value={value}
            onChange={e => onChange(e.target.value)}
            className="bg-slate-900/50 border border-slate-700/50 group-focus-within:border-violet-500/50 rounded-lg p-3 text-slate-200 w-full focus:ring-2 focus:ring-violet-500/20 outline-none transition-all appearance-none cursor-pointer hover:bg-slate-800/50"
        >
            <option value="">Select...</option>
            {options && Array.isArray(options) && options.map(opt => (
                <option key={opt[idKey]} value={opt[idKey]}>{opt.name}</option>
            ))}
        </select>
        {value && <div className="text-[10px] text-slate-500 font-mono text-right">ID: {value.substring(0, 8)}...</div>}
    </div>
);

export default MlCompose;
