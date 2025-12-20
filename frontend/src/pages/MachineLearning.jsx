import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Play, Activity, Layers, Server } from 'lucide-react';

const MachineLearning = () => {
    const [datasets, setDatasets] = useState([]);
    const [selectedDataset, setSelectedDataset] = useState('');
    const [trainingConfig, setTrainingConfig] = useState({
        epochs: 10,
        batch_size: 32,
        learning_rate: 0.001,
        window_size: 10
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

    // Mock Chart Data Updates (In real app, parse this from logs or status)
    useEffect(() => {
        if (jobStatus === 'RUNNING') {
            const interval = setInterval(() => {
                setChartData(prev => {
                    const epoch = prev.length + 1;
                    // Simulate loss going down
                    const loss = Math.max(0.1, 2.0 * Math.exp(-0.1 * epoch) + (Math.random() * 0.1));
                    return [...prev, { epoch, loss }];
                });
            }, 1000);
            return () => clearInterval(interval);
        }
    }, [jobStatus]);


    const handleStartTraining = async () => {
        if (!selectedDataset) return;

        setChartData([]); // Reset chart
        setJobStatus('PENDING');

        try {
            const payload = {
                dataset_id: selectedDataset,
                model_architecture: [
                    { type: "input", layer: { type: "Input", params: { shape: [trainingConfig.window_size, 5] } } }, // 5 features
                    { type: "hidden", layer: { type: "Dense", params: { units: 64, activation: "relu" } } },
                    { type: "output", layer: { type: "Dense", params: { units: 3, activation: "linear" } } }
                ],
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
        if (!jobId || jobStatus === 'COMPLETED' || jobStatus === 'FAILED') return;

        const interval = setInterval(async () => {
            try {
                const res = await fetch(`http://localhost:8000/api/training/status/${jobId}`);
                if (res.ok) {
                    const data = await res.json();
                    setJobStatus(data.status);
                    if (data.status !== jobStatus) {
                        setLogs(prev => [...prev, `Status info: ${data.status}`]);
                    }
                }
            } catch (err) {
                console.error(err);
            }
        }, 2000);

        return () => clearInterval(interval);
    }, [jobId, jobStatus]);

    return (
        <div className="p-6 text-slate-200">
            <header className="mb-8">
                <h1 className="text-3xl font-bold flex items-center gap-3">
                    <Activity className="text-blue-500" />
                    Machine Learning Studio
                </h1>
                <p className="text-slate-400 mt-2">Train Reinforcement Learning agents on your curated datasets.</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* Configuration Panel */}
                <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                    <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                        <Server size={20} /> Configuration
                    </h2>

                    <div className="space-y-4">
                        <div>
                            <label className="block text-sm font-medium text-slate-400 mb-1">Select Dataset</label>
                            <select
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm text-slate-200"
                                value={selectedDataset}
                                onChange={(e) => setSelectedDataset(e.target.value)}
                            >
                                <option value="" disabled>Select a dataset...</option>
                                {datasets.map(ds => (
                                    <option key={ds.dataset_id} value={ds.dataset_id}>
                                        {ds.name} ({ds.sources.length} sources)
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Epochs</label>
                                <input
                                    type="number"
                                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm"
                                    value={trainingConfig.epochs}
                                    onChange={(e) => setTrainingConfig({ ...trainingConfig, epochs: parseInt(e.target.value) })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Batch Size</label>
                                <input
                                    type="number"
                                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm"
                                    value={trainingConfig.batch_size}
                                    onChange={(e) => setTrainingConfig({ ...trainingConfig, batch_size: parseInt(e.target.value) })}
                                />
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Learning Rate</label>
                                <input
                                    type="number"
                                    step="0.0001"
                                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm"
                                    value={trainingConfig.learning_rate}
                                    onChange={(e) => setTrainingConfig({ ...trainingConfig, learning_rate: parseFloat(e.target.value) })}
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-slate-400 mb-1">Window Size</label>
                                <input
                                    type="number"
                                    className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-sm"
                                    value={trainingConfig.window_size}
                                    onChange={(e) => setTrainingConfig({ ...trainingConfig, window_size: parseInt(e.target.value) })}
                                />
                            </div>
                        </div>

                        <button
                            onClick={handleStartTraining}
                            disabled={!selectedDataset || jobStatus === 'RUNNING'}
                            className={`w-full mt-4 flex items-center justify-center gap-2 py-3 rounded-lg font-medium transition-colors
                                ${jobStatus === 'RUNNING' ? 'bg-slate-600 cursor-not-allowed' : 'bg-blue-600 hover:bg-blue-500 text-white'}
                            `}
                        >
                            <Play size={18} />
                            {jobStatus === 'RUNNING' ? 'Start Training' : 'Start Training'}
                        </button>
                    </div>
                </div>

                {/* Status & Architecture Panel */}
                <div className="lg:col-span-2 space-y-6">

                    {/* Training Metrics Chart */}
                    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 h-[300px]">
                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            Training Progress (Loss)
                        </h2>
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="epoch" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }}
                                    itemStyle={{ color: '#e2e8f0' }}
                                />
                                <Line type="monotone" dataKey="loss" stroke="#ef4444" strokeWidth={2} dot={false} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>

                    {/* Architecture Preview (Static for MVP) */}
                    <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
                        <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                            <Layers size={20} /> Model Architecture
                        </h2>
                        <div className="flex items-center gap-4 overflow-x-auto pb-2">
                            <div className="px-4 py-3 bg-slate-900 rounded border border-slate-600 min-w-[100px] text-center">
                                <span className="text-xs text-slate-400 block">Input</span>
                                <span className="font-bold">Window ({trainingConfig.window_size})</span>
                            </div>
                            <span className="text-slate-500">→</span>
                            <div className="px-4 py-3 bg-slate-900 rounded border border-blue-500/30 min-w-[100px] text-center">
                                <span className="text-xs text-blue-400 block">Hidden</span>
                                <span className="font-bold">Dense (64)</span>
                            </div>
                            <span className="text-slate-500">→</span>
                            <div className="px-4 py-3 bg-slate-900 rounded border border-green-500/30 min-w-[100px] text-center">
                                <span className="text-xs text-green-400 block">Output</span>
                                <span className="font-bold">Actions (3)</span>
                            </div>
                        </div>
                    </div>

                    {/* Console / Logs */}
                    <div className="bg-slate-950 rounded-xl p-6 border border-slate-700 font-mono text-sm h-[200px] overflow-y-auto">
                        <div className="mb-2 text-slate-500 uppercase text-xs tracking-wider">Job Console</div>
                        {logs.length === 0 ? (
                            <span className="text-slate-600 italic">Ready to train...</span>
                        ) : (
                            logs.map((log, i) => (
                                <div key={i} className="mb-1">
                                    <span className="text-slate-500 mr-2">[{new Date().toLocaleTimeString()}]</span>
                                    <span className={log.includes('Error') ? 'text-red-400' : 'text-green-400'}>{log}</span>
                                </div>
                            ))
                        )}
                        {jobStatus && (
                            <div className="mt-4 pt-4 border-t border-slate-800">
                                Current Status: <span className="font-bold text-white">{jobStatus}</span>
                            </div>
                        )}
                    </div>

                </div>
            </div>
        </div>
    );
};

export default MachineLearning;
