import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Save, HelpCircle } from 'lucide-react';

const MlCompose = () => {
    const navigate = useNavigate();

    // Form State
    const [sessionName, setSessionName] = useState('');
    const [functions, setFunctions] = useState([]);
    const [models, setModels] = useState([]);
    const [processes, setProcesses] = useState([]);

    const [selectedFunction, setSelectedFunction] = useState('');
    const [selectedModel, setSelectedModel] = useState('');
    const [selectedProcess, setSelectedProcess] = useState('');

    // Load available options
    useEffect(() => {
        const loadData = async () => {
            try {
                const [fRes, mRes, pRes] = await Promise.all([
                    fetch('http://localhost:8000/api/ml/studio/functions'),
                    fetch('http://localhost:8000/api/ml/studio/models'),
                    fetch('http://localhost:8000/api/ml/studio/processes')
                ]);

                setFunctions(await fRes.json());
                setModels(await mRes.json());
                setProcesses(await pRes.json());
            } catch (err) {
                console.error("Failed to load options", err);
            }
        };
        loadData();
    }, []);

    const handleSave = async () => {
        if (!sessionName || !selectedFunction || !selectedModel || !selectedProcess) return;

        try {
            const res = await fetch('http://localhost:8000/api/ml/studio/sessions', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: sessionName,
                    function_id: selectedFunction,
                    model_id: selectedModel,
                    process_id: selectedProcess
                })
            });

            if (res.ok) {
                navigate('/ml/studio');
            } else {
                alert("Failed to create session");
            }
        } catch (err) {
            console.error(err);
        }
    };

    return (
        <div className="p-8 text-slate-200 max-w-4xl mx-auto">
            <button
                onClick={() => navigate('/ml/studio')}
                className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-6 transition-colors"
            >
                <ArrowLeft size={18} /> Back to Studio
            </button>

            <header className="mb-8 border-b border-slate-700 pb-6">
                <h1 className="text-3xl font-bold mb-2">Compose Training Session</h1>
                <p className="text-slate-400">Combine a Reward Function, Model Architecture, and Training Process into a reusable Session.</p>
            </header>

            <div className="space-y-8">
                {/* Name */}
                <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <label className="block text-sm font-medium text-slate-400 mb-2">Session Name</label>
                    <input
                        type="text"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none transition-all"
                        placeholder="e.g. BTC Trend Follower v1"
                        value={sessionName}
                        onChange={e => setSessionName(e.target.value)}
                    />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    {/* Function Selection */}
                    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-semibold text-lg flex items-center gap-2">
                                <span className="w-6 h-6 rounded-full bg-red-500/20 text-red-500 flex items-center justify-center text-xs font-bold">1</span>
                                Reward Function
                            </h3>
                            {/* <button className="text-xs text-blue-400">+ New</button> */}
                        </div>
                        <select
                            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200 mb-2"
                            value={selectedFunction}
                            onChange={(e) => setSelectedFunction(e.target.value)}
                        >
                            <option value="" disabled>Select Function...</option>
                            {functions.map(f => (
                                <option key={f.function_id} value={f.function_id}>{f.name}</option>
                            ))}
                        </select>
                        <p className="text-xs text-slate-500">Defines how the agent is rewarded for its actions.</p>
                    </div>

                    {/* Model Selection */}
                    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-semibold text-lg flex items-center gap-2">
                                <span className="w-6 h-6 rounded-full bg-blue-500/20 text-blue-500 flex items-center justify-center text-xs font-bold">2</span>
                                Model Architecture
                            </h3>
                            {/* <button className="text-xs text-blue-400">+ New</button> */}
                        </div>
                        <select
                            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200 mb-2"
                            value={selectedModel}
                            onChange={(e) => setSelectedModel(e.target.value)}
                        >
                            <option value="" disabled>Select Model...</option>
                            {models.map(m => (
                                <option key={m.model_id} value={m.model_id}>{m.name}</option>
                            ))}
                        </select>
                        <p className="text-xs text-slate-500">Neural Network layers and configuration.</p>
                    </div>

                    {/* Process Selection */}
                    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="font-semibold text-lg flex items-center gap-2">
                                <span className="w-6 h-6 rounded-full bg-green-500/20 text-green-500 flex items-center justify-center text-xs font-bold">3</span>
                                Training Process
                            </h3>
                            {/* <button className="text-xs text-blue-400">+ New</button> */}
                        </div>
                        <select
                            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200 mb-2"
                            value={selectedProcess}
                            onChange={(e) => setSelectedProcess(e.target.value)}
                        >
                            <option value="" disabled>Select Process...</option>
                            {processes.map(p => (
                                <option key={p.process_id} value={p.process_id}>{p.name}</option>
                            ))}
                        </select>
                        <p className="text-xs text-slate-500">Hyperparameters and Training loop settings.</p>
                    </div>
                </div>

                <div className="flex justify-end pt-6 border-t border-slate-700">
                    <button
                        onClick={handleSave}
                        disabled={!sessionName || !selectedFunction || !selectedModel || !selectedProcess}
                        className={`flex items-center gap-2 px-6 py-3 rounded-lg font-bold transition-all shadow-lg
                            ${(!sessionName || !selectedFunction || !selectedModel || !selectedProcess)
                                ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                                : 'bg-green-600 hover:bg-green-500 text-white shadow-green-500/20'}
                        `}
                    >
                        <Save size={20} /> Create Session
                    </button>
                </div>
            </div>
        </div>
    );
};

export default MlCompose;
