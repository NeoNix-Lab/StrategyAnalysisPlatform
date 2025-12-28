
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Play, CheckCircle, Database, Calendar } from 'lucide-react';

const MlModelRegistry = () => {
    const navigate = useNavigate();
    const [models, setModels] = useState([]);
    const [loading, setLoading] = useState(true);
    const [selectedModel, setSelectedModel] = useState(null);
    const [datasets, setDatasets] = useState([]);
    const [testModalOpen, setTestModalOpen] = useState(false);
    const [targetDataset, setTargetDataset] = useState('');

    useEffect(() => {
        fetchModels();
        fetchDatasets();
    }, []);

    const fetchModels = async () => {
        try {
            // We fetch all sessions and flatten iterations that are COMPLETED
            const response = await fetch('/api/ml/studio/sessions');
            if (response.ok) {
                const data = await response.json();
                const completedIterations = [];

                // We need to fetch details for each session to get iterations? 
                // The list_sessions endpoint might only return summary.
                // Let's rely on list_sessions first, if it doesn't have iterations, we might need another way.
                // Actually list_sessions returns summary. We might need a new endpoint /models/completed or client-side aggregation involving N calls (bad).
                // Let's try to assume we can get them or add an endpoint. 
                // For now, I will use a dedicated endpoint "GET /api/ml/studio/models" which I will implement in backend.

                const modelsEx = await fetch('/api/ml/studio/trained-models'); // New Endpoint
                if (modelsEx.ok) {
                    setModels(await modelsEx.json());
                }
            }
        } catch (error) {
            console.error(error);
        } finally {
            setLoading(false);
        }
    };

    const fetchDatasets = async () => {
        const res = await fetch('/api/datasets');
        if (res.ok) setDatasets(await res.json());
    };

    const openTestModal = (model) => {
        setSelectedModel(model);
        setTestModalOpen(true);
    };

    const handleRunTest = async () => {
        if (!selectedModel || !targetDataset) return;

        try {
            const res = await fetch('/api/ml/studio/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    source_iteration_id: selectedModel.iteration_id,
                    target_dataset_id: targetDataset
                })
            });

            if (res.ok) {
                const data = await res.json();
                // Navigate to the new test run
                navigate(`/ml/studio/session/${data.session_id}/run/${data.iteration_id}`);
            }
        } catch (e) {
            console.error(e);
        }
    };

    return (
        <div className="text-slate-200">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <Box className="text-purple-400" /> Model Registry
            </h2>

            {loading ? (
                <div className="text-slate-500">Loading trained models...</div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {models.map(model => (
                        <div key={model.iteration_id} className="bg-slate-800 border border-slate-700 rounded-xl p-5 hover:border-purple-500/50 transition-all">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="font-semibold text-lg text-slate-100">{model.name}</h3>
                                    <span className="text-xs text-slate-500 font-mono">{model.iteration_id.slice(0, 8)}</span>
                                </div>
                                <div className="bg-green-500/10 text-green-400 px-2 py-1 rounded-full text-xs font-medium border border-green-500/20">
                                    READY
                                </div>
                            </div>

                            <div className="space-y-3 mb-6">
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-slate-500">Algorithm</span>
                                    <span className="text-slate-300">{model.algorithm}</span>
                                </div>
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-slate-500">Trained On</span>
                                    <span className="text-slate-300">{model.dataset}</span>
                                </div>
                                <div className="flex items-center justify-between text-sm">
                                    <span className="text-slate-500">Performance</span>
                                    <span className="text-purple-400 font-mono">
                                        R: {model.metrics?.final?.reward?.toFixed(2) || 'N/A'} | L: {model.metrics?.final?.loss?.toFixed(4) || '0'}
                                    </span>
                                </div>
                            </div>

                            <button
                                onClick={() => openTestModal(model)}
                                className="w-full py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg flex items-center justify-center gap-2 transition-colors border border-slate-600"
                            >
                                <Play size={16} className="text-purple-400" /> Test on Dataset
                            </button>
                        </div>
                    ))}

                    {models.length === 0 && (
                        <div className="col-span-full py-12 text-center bg-slate-800/50 rounded-xl border border-dashed border-slate-700">
                            <Box size={48} className="mx-auto text-slate-600 mb-4" />
                            <p className="text-slate-500">No trained models found.</p>
                            <p className="text-slate-600 text-sm mt-1">Complete a training session to see models here.</p>
                        </div>
                    )}
                </div>
            )}

            {/* Test Modal */}
            {testModalOpen && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50">
                    <div className="bg-slate-900 border border-slate-700 p-6 rounded-xl w-full max-w-md shadow-2xl">
                        <h3 className="text-xl font-bold mb-4">Run Inference Test</h3>
                        <p className="text-slate-400 text-sm mb-6">
                            Test model <span className="text-white font-mono">{selectedModel?.name}</span> on a new dataset.
                            Weights will be loaded and training (backprop) will be disabled.
                        </p>

                        <div className="mb-6">
                            <label className="block text-sm font-medium text-slate-400 mb-2">Select Target Dataset</label>
                            <select
                                className="w-full bg-slate-800 border border-slate-700 rounded-lg px-4 py-2 text-white focus:ring-2 focus:ring-purple-500 outline-none"
                                value={targetDataset}
                                onChange={(e) => setTargetDataset(e.target.value)}
                            >
                                <option value="">-- Choose Dataset --</option>
                                {datasets.map(d => (
                                    <option key={d.dataset_id} value={d.dataset_id}>
                                        {d.name} ({d.dataset_id.slice(0, 8)})
                                    </option>
                                ))}
                            </select>
                        </div>

                        <div className="flex justify-end gap-3">
                            <button
                                onClick={() => setTestModalOpen(false)}
                                className="px-4 py-2 text-slate-400 hover:text-white"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={handleRunTest}
                                disabled={!targetDataset}
                                className="px-4 py-2 bg-purple-600 hover:bg-purple-500 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg font-medium"
                            >
                                Start Test Run
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default MlModelRegistry;
