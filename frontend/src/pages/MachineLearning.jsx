import React, { useState, useEffect } from 'react';
import { Play, Activity, Server, LayoutTemplate } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import ModelBuilder from '../components/ml/ModelBuilder';
import Hyperparameters from '../components/ml/Hyperparameters';

const MachineLearning = () => {
    const [datasets, setDatasets] = useState([]);
    const [selectedDataset, setSelectedDataset] = useState('');

    // Model Architecture State (Hidden Layers)
    const [modelLayers, setModelLayers] = useState([
        { type: 'Dense', params: { units: 64, activation: 'relu' } }
    ]);

    // Hyperparams State
    const [trainingConfig, setTrainingConfig] = useState({
        epochs: 50,
        batch_size: 32,
        learning_rate: 0.001,
        window_size: 10,
        gamma: 0.99,
        tau: 0.005,
        epsilon_start: 1.0,
        epsilon_end: 0.01
    });

    const [jobId, setJobId] = useState(null);
    const [jobStatus, setJobStatus] = useState(null);
    const [logs, setLogs] = useState([]);
    const [chartData, setChartData] = useState([]);

    // Fetch Datasets
    useEffect(() => {
        fetch('http://localhost:8000/api/datasets/')
            .then(res => res.json())
            .then(data => {
                setDatasets(data);
                if (data.length > 0) setSelectedDataset(data[0].dataset_id);
            })
            .catch(err => {
                console.error("Failed to fetch datasets:", err);
                setLogs(prev => [...prev, "Error: Failed to fetch datasets"]);
            });
    }, []);

    // Mock Chart Data Updates
    useEffect(() => {
        if (jobStatus === 'RUNNING') {
            const interval = setInterval(() => {
                setChartData(prev => {
                    const epoch = prev.length + 1;
                    const loss = Math.max(0.1, 2.0 * Math.exp(-0.1 * epoch) + (Math.random() * 0.1));
                    return [...prev, { epoch, loss }];
                });
            }, 1000);
            return () => clearInterval(interval);
        }
    }, [jobStatus]);

    const handleStartTraining = async () => {
        if (!selectedDataset) return;

        setChartData([]);
        setJobStatus('PENDING');

        // Construct Architecture
        const fullArchitecture = [
            { type: "input", layer: { type: "Input", params: { shape: [trainingConfig.window_size, 5] } } }, // Hardcoded 5 features for now
            ...modelLayers.map(l => ({ type: "hidden", layer: { type: l.type, params: l.params } })),
            { type: "output", layer: { type: "Dense", params: { units: 3, activation: "linear" } } }
        ];

        try {
            const payload = {
                dataset_id: selectedDataset,
                model_architecture: fullArchitecture,
                training_params: trainingConfig
            };

            const response = await fetch('http://localhost:8000/api/training/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error('Failed to start training');

            const data = await response.json();
            setJobId(data.job_id);
            setLogs(prev => [...prev, `Job started: ${data.job_id}`]);

        } catch (error) {
            console.error(error);
            setLogs(prev => [...prev, `Error: ${error.message}`]);
            setJobStatus('FAILED');
        }
    };

    // Polling Status
    useEffect(() => {
        if (!jobId || ['COMPLETED', 'FAILED'].includes(jobStatus)) return;
        const interval = setInterval(async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/training/status/${jobId}`);
                if (res.ok) {
                    const data = await res.json();
                    setJobStatus(data.status);
                    if (data.status !== jobStatus) setLogs(prev => [...prev, `Status info: ${data.status}`]);
                }
            } catch (err) { console.error(err); }
        }, 2000);
        return () => clearInterval(interval);
    }, [jobId, jobStatus]);

    return (
        <div className="p-6 text-slate-200 h-full overflow-y-auto">
            <header className="mb-8">
                <h1 className="text-3xl font-bold flex items-center gap-3">
                    <Activity className="text-blue-500" />
                    Quick Train Studio
                </h1>
                <p className="text-slate-400 mt-2">Design, Configure, and Train your RL Agents.</p>
            </header>

            <div className="grid grid-cols-12 gap-6 h-[calc(100vh-180px)]">

                {/* Left Column: Config & Hyperparams (3 cols) */}
                <div className="col-span-3 flex flex-col gap-6">
                    {/* Dataset Selection */}
                    <div className="bg-slate-800 rounded-xl p-4 border border-slate-700">
                        <h3 className="text-sm font-medium text-slate-400 mb-2">Dataset</h3>
                        <select
                            className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200"
                            value={selectedDataset}
                            onChange={(e) => setSelectedDataset(e.target.value)}
                        >
                            <option value="" disabled>Select a dataset...</option>
                            {datasets.map(ds => (
                                <option key={ds.dataset_id} value={ds.dataset_id}>{ds.name}</option>
                            ))}
                        </select>
                    </div>

                    {/* Hyperparameters Component */}
                    <div className="flex-1 min-h-0">
                        <Hyperparameters config={trainingConfig} setConfig={setTrainingConfig} />
                    </div>
                </div>

                {/* Middle Column: Model Builder (4 cols) */}
                <div className="col-span-4 h-full">
                    <ModelBuilder layers={modelLayers} setLayers={setModelLayers} />
                </div>

                {/* Right Column: Training Control & Monitor (5 cols) */}
                <div className="col-span-5 flex flex-col gap-6 h-full">

                    {/* Training Monitor */}
                    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 flex-1 flex flex-col">
                        <div className="flex justify-between items-center mb-4">
                            <h2 className="text-xl font-semibold flex items-center gap-2">
                                <Activity size={20} className="text-blue-400" /> Training Monitor
                            </h2>
                            <div className={`px-3 py-1 rounded-full text-sm font-medium ${jobStatus === 'RUNNING' ? 'bg-blue-900/50 text-blue-400 animate-pulse' :
                                jobStatus === 'COMPLETED' ? 'bg-green-900/50 text-green-400' :
                                    jobStatus === 'FAILED' ? 'bg-red-900/50 text-red-400' :
                                        'bg-slate-700 text-slate-400'
                                }`}>
                                {jobStatus || 'IDLE'}
                            </div>
                        </div>

                        <div className="flex-1 bg-slate-900 rounded-lg p-2 border border-slate-700 mb-4 min-h-[200px]">
                            {chartData.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={chartData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis dataKey="epoch" stroke="#94a3b8" />
                                        <YAxis stroke="#94a3b8" />
                                        <Tooltip
                                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }}
                                            itemStyle={{ color: '#e2e8f0' }}
                                        />
                                        <Line type="monotone" dataKey="loss" stroke="#60a5fa" strokeWidth={2} dot={false} />
                                    </LineChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="h-full flex items-center justify-center text-slate-600">
                                    No chart data available
                                </div>
                            )}
                        </div>

                        {/* Logs Console */}
                        <div className="h-32 bg-black/50 rounded border border-slate-800 p-2 font-mono text-xs overflow-y-auto">
                            {logs.map((log, i) => (
                                <div key={i} className="text-slate-400 mb-1">{`> ${log}`}</div>
                            ))}
                            {logs.length === 0 && <span className="text-slate-600">System ready...</span>}
                        </div>

                        <button
                            onClick={handleStartTraining}
                            disabled={!selectedDataset || jobStatus === 'RUNNING'}
                            className={`w-full mt-4 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors shadow-lg
                                ${jobStatus === 'RUNNING' ? 'bg-slate-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 text-white shadow-blue-500/20'}
                            `}
                        >
                            <Play size={20} fill="currentColor" />
                            {jobStatus === 'RUNNING' ? 'Training in Progress...' : 'Start Training Session'}
                        </button>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default MachineLearning;
