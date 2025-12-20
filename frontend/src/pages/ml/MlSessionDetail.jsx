import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { ArrowLeft, Play, Box, Database, Clock, Plus } from 'lucide-react';

const MlSessionDetail = () => {
    const { sessionId } = useParams();
    const navigate = useNavigate();
    const [session, setSession] = useState(null);
    const [loading, setLoading] = useState(true);
    const [datasets, setDatasets] = useState([]);

    // New Iteration State
    const [showNewIter, setShowNewIter] = useState(false);
    const [selectedDataset, setSelectedDataset] = useState('');
    const [splitConfig, setSplitConfig] = useState({ train: 0.7, test: 0.2, work: 0.1 });

    useEffect(() => {
        Promise.all([
            fetch(`http://localhost:8000/api/ml/studio/sessions/${sessionId}`).then(res => res.json()),
            fetch('http://localhost:8000/api/datasets/').then(res => res.json())
        ]).then(([sessionData, datasetsData]) => {
            setSession(sessionData);
            setDatasets(datasetsData);
            setLoading(false);
        }).catch(err => console.error(err));
    }, [sessionId]);

    const handleCreateIteration = async () => {
        if (!selectedDataset) return;

        try {
            const res = await fetch('http://localhost:8000/api/ml/studio/iterations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: sessionId,
                    dataset_id: selectedDataset,
                    split_config: splitConfig
                })
            });

            if (res.ok) {
                // Refresh session or navigate? Maybe stay and show the new iteration
                // For now, reload
                window.location.reload();
            }
        } catch (err) {
            console.error(err);
        }
    };

    if (loading) return <div className="p-8 text-slate-400">Loading session...</div>;
    if (!session) return <div className="p-8 text-red-400">Session not found</div>;

    return (
        <div className="p-8 text-slate-200">
            <button
                onClick={() => navigate('/ml/studio')}
                className="flex items-center gap-2 text-slate-400 hover:text-slate-200 mb-6 transition-colors"
            >
                <ArrowLeft size={18} /> Back to Studio
            </button>

            {/* Header */}
            <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 mb-8">
                <div className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold mb-2">{session.name}</h1>
                        <div className="flex gap-4 text-sm text-slate-400">
                            <span className="flex items-center gap-1"><Box size={14} /> Model: {session.model?.name}</span>
                            <span className="flex items-center gap-1"><Clock size={14} /> Process: {session.process?.name}</span>
                        </div>
                    </div>
                    <div className="px-3 py-1 bg-slate-700 rounded text-sm text-slate-300">
                        {session.status}
                    </div>
                </div>
            </div>

            {/* Iterations List */}
            <div className="mb-6 flex justify-between items-center">
                <h2 className="text-xl font-semibold">Iterations</h2>
                <button
                    onClick={() => setShowNewIter(!showNewIter)}
                    className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg text-sm font-medium"
                >
                    <Plus size={16} /> New Iteration
                </button>
            </div>

            {/* New Iteration Form */}
            {showNewIter && (
                <div className="bg-slate-800/50 border border-slate-700 p-6 rounded-xl mb-8 animate-in fade-in slide-in-from-top-4">
                    <h3 className="font-semibold mb-4">Launch New Iteration</h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-4">
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Select Dataset</label>
                            <select
                                className="w-full bg-slate-900 border border-slate-600 rounded p-2 text-sm text-slate-200"
                                value={selectedDataset}
                                onChange={(e) => setSelectedDataset(e.target.value)}
                            >
                                <option value="" disabled>Choose a dataset...</option>
                                {datasets.map(d => (
                                    <option key={d.dataset_id} value={d.dataset_id}>{d.name}</option>
                                ))}
                            </select>
                        </div>
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Data Split (Train/Test/Work)</label>
                            <div className="flex gap-2">
                                <input type="number" step="0.1" className="w-[33%] bg-slate-900 border border-slate-600 rounded p-2 text-sm" value={splitConfig.train} onChange={e => setSplitConfig({ ...splitConfig, train: parseFloat(e.target.value) })} />
                                <input type="number" step="0.1" className="w-[33%] bg-slate-900 border border-slate-600 rounded p-2 text-sm" value={splitConfig.test} onChange={e => setSplitConfig({ ...splitConfig, test: parseFloat(e.target.value) })} />
                                <input type="number" step="0.1" className="w-[33%] bg-slate-900 border border-slate-600 rounded p-2 text-sm" value={splitConfig.work} onChange={e => setSplitConfig({ ...splitConfig, work: parseFloat(e.target.value) })} />
                            </div>
                        </div>
                    </div>
                    <div className="flex justify-end">
                        <button
                            onClick={handleCreateIteration}
                            disabled={!selectedDataset}
                            className={`px-4 py-2 rounded font-medium ${!selectedDataset ? 'bg-slate-700 text-slate-500' : 'bg-green-600 hover:bg-green-500 text-white'}`}
                        >
                            Create & Run
                        </button>
                    </div>
                </div>
            )}

            {/* List */}
            {/* Fetching iterations is missing in GET /sessions/{id}, I need to ensure it returns them or fetch separately. 
                 The current backend implementation of get_session DOES return "iterations_count", but not the list.
                 I should probably update the backend or fetch them. 
                 Wait, I will update the frontend to assume empty for now or fix backend. 
                 Let's fix backend to return iterations list in `get_session`.
             */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                <table className="w-full text-left text-sm text-slate-400">
                    <thead className="bg-slate-900/50 text-slate-200 uppercase text-xs">
                        <tr>
                            <th className="px-6 py-3">Iteration ID</th>
                            <th className="px-6 py-3">Dataset</th>
                            <th className="px-6 py-3">Status</th>
                            <th className="px-6 py-3">Created</th>
                            <th className="px-6 py-3 text-right">Action</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700">
                        {/* 
                         TODO: Iterate over session.iterations
                         For now, placeholder.
                        */}
                        {session.iterations?.map(iter => (
                            <tr key={iter.iteration_id} className="hover:bg-slate-700/30 transition-colors">
                                <td className="px-6 py-4 font-mono text-xs">{iter.iteration_id.slice(0, 8)}...</td>
                                <td className="px-6 py-4">{iter.dataset_name || 'Dataset'}</td>
                                <td className="px-6 py-4">
                                    <span className={`px-2 py-1 rounded-full text-xs ${iter.status === 'COMPLETED' ? 'bg-green-500/10 text-green-400' :
                                            iter.status === 'RUNNING' ? 'bg-blue-500/10 text-blue-400 animate-pulse' :
                                                'bg-slate-700 text-slate-400'
                                        }`}>
                                        {iter.status}
                                    </span>
                                </td>
                                <td className="px-6 py-4">{new Date().toLocaleDateString()}</td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => navigate(`/ml/studio/session/${sessionId}/run/${iter.iteration_id}`)}
                                        className="text-blue-400 hover:text-blue-300 font-medium"
                                    >
                                        Open &rarr;
                                    </button>
                                </td>
                            </tr>
                        ))}
                        {(!session.iterations || session.iterations.length === 0) && (
                            <tr>
                                <td colSpan="5" className="px-6 py-8 text-center text-slate-500">
                                    No iterations yet. Launch one above.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

        </div>
    );
};

export default MlSessionDetail;
