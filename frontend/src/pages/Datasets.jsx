import React, { useState, useEffect } from 'react';
import { Database, Plus, Trash2, Check, X, Layers, Search, Calendar } from 'lucide-react';

const Datasets = () => {
    const [datasets, setDatasets] = useState([]);
    const [runs, setRuns] = useState([]);
    const [view, setView] = useState('list'); // 'list' | 'create'

    // Form State
    const [newName, setNewName] = useState('');
    const [newDesc, setNewDesc] = useState('');
    const [selectedRuns, setSelectedRuns] = useState([]); // List of run_ids

    const [datasetDetails, setDatasetDetails] = useState(null); // Selected dataset for details view

    useEffect(() => {
        fetchDatasets();
        fetchRuns();
    }, []);

    const fetchDatasets = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/datasets/');
            const data = await res.json();
            setDatasets(data);
        } catch (err) {
            console.error(err);
        }
    };

    const fetchRuns = async () => {
        try {
            const res = await fetch('http://localhost:8000/api/runs/');
            const data = await res.json();
            setRuns(data);
        } catch (err) {
            console.error(err);
        }
    };

    const handleCreateDataset = async () => {
        if (!newName || selectedRuns.length === 0) return;

        // Build sources list
        const sources = selectedRuns.map(runId => {
            const run = runs.find(r => r.run_id === runId);
            return {
                run_id: runId,
                symbol: run?.symbol,
                timeframe: run?.timeframe
                // start/end time logic can be added later
            };
        });

        const payload = {
            name: newName,
            description: newDesc,
            sources: sources,
            feature_config: ["open", "high", "low", "close", "volume"] // Default for now
        };

        try {
            const res = await fetch('http://localhost:8000/api/datasets/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                fetchDatasets();
                setView('list');
                setNewName('');
                setNewDesc('');
                setSelectedRuns([]);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleDelete = async (id) => {
        if (!confirm('Are you sure?')) return;
        try {
            await fetch(`http://localhost:8000/api/datasets/${id}`, { method: 'DELETE' });
            fetchDatasets();
            if (datasetDetails?.dataset_id === id) setDatasetDetails(null);
        } catch (err) {
            console.error(err);
        }
    };

    const toggleRunSelection = (runId) => {
        if (selectedRuns.includes(runId)) {
            setSelectedRuns(selectedRuns.filter(id => id !== runId));
        } else {
            setSelectedRuns([...selectedRuns, runId]);
        }
    };

    return (
        <div className="p-6 text-slate-200 h-full flex flex-col">
            <header className="mb-6 flex justify-between items-center">
                <div>
                    <h1 className="text-3xl font-bold flex items-center gap-3">
                        <Database className="text-purple-500" />
                        Dataset Management
                    </h1>
                    <p className="text-slate-400 mt-2">Curate and manage training datasets from strategy runs.</p>
                </div>
                {view === 'list' && (
                    <button
                        onClick={() => setView('create')}
                        className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
                    >
                        <Plus size={18} /> New Dataset
                    </button>
                )}
            </header>

            <div className="flex-1 flex gap-6 overflow-hidden">

                {/* Mode: LIST */}
                {view === 'list' && (
                    <>
                        <div className="w-1/3 bg-slate-800 rounded-xl border border-slate-700 overflow-hidden flex flex-col">
                            <div className="p-4 border-b border-slate-700 bg-slate-900/50">
                                <h3 className="font-semibold text-slate-300">Available Datasets</h3>
                            </div>
                            <div className="flex-1 overflow-y-auto p-2 space-y-2">
                                {datasets.length === 0 && <div className="text-slate-500 text-center py-8">No datasets found.</div>}
                                {datasets.map(ds => (
                                    <div
                                        key={ds.dataset_id}
                                        onClick={() => setDatasetDetails(ds)}
                                        className={`p-3 rounded-lg cursor-pointer border transition-colors ${datasetDetails?.dataset_id === ds.dataset_id ? 'bg-purple-900/20 border-purple-500/50' : 'bg-slate-900/50 border-slate-700 hover:border-slate-600'}`}
                                    >
                                        <div className="flex justify-between items-start">
                                            <span className="font-medium text-slate-200">{ds.name}</span>
                                            <span className="text-xs text-slate-500">{new Date(ds.created_utc).toLocaleDateString()}</span>
                                        </div>
                                        <div className="text-xs text-slate-400 mt-1 truncate">{ds.description || "No description"}</div>
                                        <div className="mt-2 flex gap-2">
                                            <span className="text-xs bg-slate-800 px-2 py-0.5 rounded text-slate-400">{ds.sources.length} Runs</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>

                        <div className="w-2/3 bg-slate-900 rounded-xl border border-slate-700 p-6 overflow-y-auto">
                            {datasetDetails ? (
                                <div>
                                    <div className="flex justify-between items-start mb-6">
                                        <div>
                                            <h2 className="text-2xl font-bold text-white mb-2">{datasetDetails.name}</h2>
                                            <p className="text-slate-400">{datasetDetails.description}</p>
                                        </div>
                                        <button
                                            onClick={() => handleDelete(datasetDetails.dataset_id)}
                                            className="text-red-400 hover:text-red-300 p-2 rounded hover:bg-red-900/20"
                                            title="Delete Dataset"
                                        >
                                            <Trash2 size={20} />
                                        </button>
                                    </div>

                                    <div className="grid grid-cols-2 gap-4 mb-8">
                                        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                                            <div className="text-slate-500 text-sm mb-1">Created</div>
                                            <div className="font-mono">{new Date(datasetDetails.created_utc).toLocaleString()}</div>
                                        </div>
                                        <div className="bg-slate-800 p-4 rounded-lg border border-slate-700">
                                            <div className="text-slate-500 text-sm mb-1">ID</div>
                                            <div className="font-mono text-xs text-slate-400 truncate" title={datasetDetails.dataset_id}>{datasetDetails.dataset_id}</div>
                                        </div>
                                    </div>

                                    <h3 className="text-lg font-semibold mb-3 flex items-center gap-2">
                                        <Layers size={18} /> Source Runs
                                    </h3>
                                    <div className="space-y-2">
                                        {datasetDetails.sources.map((src, i) => (
                                            <div key={i} className="flex items-center justify-between p-3 bg-slate-800 rounded border border-slate-700">
                                                <div className="flex items-center gap-3">
                                                    <div className="w-2 h-2 rounded-full bg-green-500"></div>
                                                    <span className="font-mono text-sm text-slate-300">{src.symbol}</span>
                                                    <span className="text-xs bg-slate-700 px-1.5 py-0.5 rounded">{src.timeframe || 'N/A'}</span>
                                                </div>
                                                <span className="font-mono text-xs text-slate-500">{src.run_id}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ) : (
                                <div className="h-full flex flex-col items-center justify-center text-slate-600">
                                    <Database size={48} className="mb-4 opacity-50" />
                                    <p>Select a dataset to view details</p>
                                </div>
                            )}
                        </div>
                    </>
                )}

                {/* Mode: CREATE */}
                {view === 'create' && (
                    <div className="w-full h-full flex flex-col bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                        <div className="flex justify-between items-center p-4 border-b border-slate-700 bg-slate-900">
                            <h2 className="text-lg font-semibold">Create New Dataset</h2>
                            <button onClick={() => setView('list')} className="text-slate-400 hover:text-white">
                                <X size={24} />
                            </button>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6">
                            <div className="max-w-4xl mx-auto space-y-8">
                                <div className="grid grid-cols-2 gap-6">
                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-2">Dataset Name</label>
                                        <input
                                            type="text"
                                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-purple-500 outline-none"
                                            placeholder="e.g. Golden Set BTC 2024"
                                            value={newName}
                                            onChange={(e) => setNewName(e.target.value)}
                                        />
                                    </div>
                                    <div>
                                        <label className="block text-sm font-medium text-slate-400 mb-2">Description</label>
                                        <input
                                            type="text"
                                            className="w-full bg-slate-900 border border-slate-700 rounded-lg p-3 text-slate-200 focus:ring-2 focus:ring-purple-500 outline-none"
                                            placeholder="Optional description..."
                                            value={newDesc}
                                            onChange={(e) => setNewDesc(e.target.value)}
                                        />
                                    </div>
                                </div>

                                <div>
                                    <h3 className="text-md font-semibold mb-4 text-slate-300">Select Source Runs</h3>
                                    <div className="bg-slate-900 rounded-lg border border-slate-700 max-h-[400px] overflow-y-auto">
                                        {runs.length === 0 && <div className="p-4 text-center text-slate-500">No runs available.</div>}
                                        {runs.map(run => (
                                            <div
                                                key={run.run_id}
                                                onClick={() => toggleRunSelection(run.run_id)}
                                                className={`p-3 border-b border-slate-800 flex items-center gap-4 cursor-pointer hover:bg-slate-800/50 transition-colors
                                                    ${selectedRuns.includes(run.run_id) ? 'bg-purple-900/10' : ''}
                                                `}
                                            >
                                                <div className={`w-5 h-5 rounded border flex items-center justify-center
                                                    ${selectedRuns.includes(run.run_id) ? 'bg-purple-600 border-purple-600' : 'border-slate-600'}
                                                `}>
                                                    {selectedRuns.includes(run.run_id) && <Check size={12} className="text-white" />}
                                                </div>
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2">
                                                        <span className="font-medium text-slate-200">[{run.strategy_name}]</span>
                                                        <span className="text-slate-300">{run.instance_name}</span>
                                                    </div>
                                                    <div className="text-xs text-slate-500 flex gap-3 mt-0.5">
                                                        <span className="flex items-center gap-1"><Calendar size={10} /> {new Date(run.start_time).toLocaleString()}</span>
                                                        <span className="font-mono text-slate-600">{run.symbol} {run.timeframe}</span>
                                                    </div>
                                                </div>
                                                <div className={`px-2 py-0.5 text-xs rounded ${run.status === 'COMPLETED' ? 'bg-green-900/30 text-green-400' : 'bg-slate-800 text-slate-500'}`}>
                                                    {run.status}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                    <div className="mt-2 text-sm text-slate-400 text-right">
                                        {selectedRuns.length} runs selected
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div className="p-4 border-t border-slate-700 bg-slate-900 flex justify-end gap-3">
                            <button
                                onClick={() => setView('list')}
                                className="px-4 py-2 rounded-lg hover:bg-slate-800 text-slate-300 transition-colors"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleCreateDataset}
                                disabled={!newName || selectedRuns.length === 0}
                                className={`px-6 py-2 rounded-lg font-medium transition-colors flex items-center gap-2
                                    ${(!newName || selectedRuns.length === 0) ? 'bg-slate-700 text-slate-500 cursor-not-allowed' : 'bg-purple-600 hover:bg-purple-500 text-white'}
                                `}
                            >
                                <Check size={18} /> Create Dataset
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default Datasets;
