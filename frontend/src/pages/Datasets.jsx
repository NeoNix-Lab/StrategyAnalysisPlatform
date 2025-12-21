import React, { useState, useEffect, useRef } from 'react';
import { Database, Plus, Trash2, Check, X, Layers, Calendar, Search, Eye, EyeOff, ChevronDown, Hash, Type } from 'lucide-react';
import './Dashboard.css';

const Datasets = () => {
    const [datasets, setDatasets] = useState([]);
    const [runs, setRuns] = useState([]);
    const [view, setView] = useState('list'); // 'list' | 'create'
    const [searchTerm, setSearchTerm] = useState('');
    const [activeTab, setActiveTab] = useState('overview');

    // Form State
    const [newName, setNewName] = useState('');
    const [newDesc, setNewDesc] = useState('');
    const [selectedRuns, setSelectedRuns] = useState([]); // List of run_ids

    const [datasetDetails, setDatasetDetails] = useState(null); // Selected dataset for details view

    useEffect(() => {
        if (!datasetDetails) setActiveTab('overview');
    }, [datasetDetails]);

    useEffect(() => {
        fetchDatasets();
        fetchRuns();
    }, []);

    const fetchDatasets = async () => {
        try {
            const res = await fetch('/api/datasets/');
            if (res.ok) {
                const data = await res.json();
                setDatasets(data);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const fetchRuns = async () => {
        try {
            const res = await fetch('/api/runs/');
            if (res.ok) {
                const data = await res.json();
                setRuns(data);
            }
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
            };
        });

        const payload = {
            name: newName,
            description: newDesc,
            sources: sources,
            feature_config: ["open", "high", "low", "close", "volume"]
        };

        try {
            const res = await fetch('/api/datasets/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            if (res.ok) {
                await fetchDatasets();
                setView('list');
                setNewName('');
                setNewDesc('');
                setSelectedRuns([]);
            }
        } catch (err) {
            console.error(err);
        }
    };

    const handleDelete = async (id, e) => {
        e.stopPropagation();
        if (!confirm('Are you sure you want to delete this dataset?')) return;
        try {
            await fetch(`/api/datasets/${id}`, { method: 'DELETE' });
            await fetchDatasets();
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

    const filteredDatasets = datasets.filter(d =>
        d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (d.description && d.description.toLowerCase().includes(searchTerm.toLowerCase()))
    );

    return (
        <div className="dashboard-container">
            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h2 style={{ fontSize: '1.8rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                        <Database className="text-purple-500" size={32} />
                        Dataset Management
                    </h2>
                    <p style={{ color: '#94a3b8', margin: '0.5rem 0 0' }}>Curate and manage training data from strategy executions.</p>
                </div>
                {view === 'list' && (
                    <button
                        className="rebuild-btn"
                        onClick={() => setView('create')}
                        style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                    >
                        <Plus size={18} /> New Dataset
                    </button>
                )}
            </div>

            {/* Content Area */}
            {view === 'list' ? (
                <div style={{ display: 'flex', gap: '1.5rem', height: 'calc(100vh - 180px)' }}>

                    {/* LEFT PANEL: Dataset List */}
                    <div className="card" style={{ width: '30%', display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
                        <div style={{ padding: '1rem', borderBottom: '1px solid #334155', background: '#1e293b' }}>
                            <div style={{ position: 'relative' }}>
                                <Search size={16} style={{ position: 'absolute', left: '10px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
                                <input
                                    type="text"
                                    placeholder="Search datasets..."
                                    value={searchTerm}
                                    onChange={e => setSearchTerm(e.target.value)}
                                    style={{
                                        width: '100%',
                                        padding: '0.5rem 0.5rem 0.5rem 2.5rem',
                                        background: '#0f172a',
                                        border: '1px solid #334155',
                                        borderRadius: '6px',
                                        color: '#e2e8f0',
                                        fontSize: '0.9rem'
                                    }}
                                />
                            </div>
                        </div>
                        <div style={{ flex: 1, overflowY: 'auto', padding: '0.5rem' }}>
                            {filteredDatasets.length === 0 && (
                                <div style={{ textAlign: 'center', padding: '2rem', color: '#64748b', fontSize: '0.9rem' }}>No datasets found.</div>
                            )}
                            {filteredDatasets.map(ds => (
                                <div
                                    key={ds.dataset_id}
                                    onClick={() => setDatasetDetails(ds)}
                                    style={{
                                        padding: '1rem',
                                        borderRadius: '8px',
                                        border: datasetDetails?.dataset_id === ds.dataset_id ? '1px solid #8b5cf6' : '1px solid transparent',
                                        background: datasetDetails?.dataset_id === ds.dataset_id ? 'rgba(139, 92, 246, 0.1)' : 'transparent',
                                        cursor: 'pointer',
                                        marginBottom: '0.5rem',
                                        transition: 'all 0.2s'
                                    }}
                                    className="hover:bg-slate-800/50"
                                >
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                        <div style={{ fontWeight: 600, color: '#f1f5f9' }}>{ds.name}</div>
                                        <div style={{ fontSize: '0.7rem', color: '#64748b' }}>{new Date(ds.created_utc).toLocaleDateString()}</div>
                                    </div>
                                    <div style={{ fontSize: '0.8rem', color: '#94a3b8', margin: '0.25rem 0' }}>{ds.description || 'No description'}</div>
                                    <div style={{ display: 'flex', gap: '0.5rem', marginTop: '0.5rem' }}>
                                        <span style={{ fontSize: '0.7rem', background: '#334155', padding: '2px 6px', borderRadius: '4px', color: '#cbd5e1' }}>
                                            {ds.sources.length} Sources
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* RIGHT PANEL: Dataset Details */}
                    <div className="card" style={{ flex: 1, padding: '2rem', overflowY: 'auto', display: 'flex', flexDirection: 'column' }}>
                        {datasetDetails ? (
                            <>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                                    <div>
                                        <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem', color: '#fff' }}>{datasetDetails.name}</h2>
                                        <p style={{ color: '#94a3b8' }}>{datasetDetails.description}</p>
                                    </div>
                                    <button
                                        onClick={(e) => handleDelete(datasetDetails.dataset_id, e)}
                                        style={{ background: 'transparent', border: '1px solid #ef4444', color: '#ef4444', padding: '0.5rem', borderRadius: '6px', cursor: 'pointer' }}
                                        title="Delete Dataset"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </div>

                                <div style={{ marginBottom: '1rem', borderBottom: '1px solid #334155', display: 'flex', gap: '2rem' }}>
                                    <button
                                        onClick={() => setActiveTab('overview')}
                                        style={{
                                            padding: '0.5rem 0',
                                            borderBottom: activeTab === 'overview' ? '2px solid #8b5cf6' : '2px solid transparent',
                                            color: activeTab === 'overview' ? '#f8fafc' : '#94a3b8',
                                            background: 'transparent', borderTop: 'none', borderLeft: 'none', borderRight: 'none', cursor: 'pointer',
                                            fontWeight: 500
                                        }}
                                    >
                                        Overview
                                    </button>
                                    <button
                                        onClick={() => setActiveTab('data')}
                                        style={{
                                            padding: '0.5rem 0',
                                            borderBottom: activeTab === 'data' ? '2px solid #8b5cf6' : '2px solid transparent',
                                            color: activeTab === 'data' ? '#f8fafc' : '#94a3b8',
                                            background: 'transparent', borderTop: 'none', borderLeft: 'none', borderRight: 'none', cursor: 'pointer',
                                            fontWeight: 500
                                        }}
                                    >
                                        Data Content
                                    </button>
                                </div>

                                <div style={{ flex: 1, overflow: 'hidden' }}>
                                    {activeTab === 'overview' ? (
                                        <div style={{ overflowY: 'auto', height: '100%' }}>
                                            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem', marginBottom: '2rem' }}>
                                                <div style={{ background: '#1e293b', padding: '1rem', borderRadius: '8px', border: '1px solid #334155' }}>
                                                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.25rem' }}>Created At</div>
                                                    <div style={{ fontFamily: 'monospace', color: '#cbd5e1' }}>{new Date(datasetDetails.created_utc).toLocaleString()}</div>
                                                </div>
                                                <div style={{ background: '#1e293b', padding: '1rem', borderRadius: '8px', border: '1px solid #334155' }}>
                                                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '0.25rem' }}>Dataset ID</div>
                                                    <div style={{ fontFamily: 'monospace', color: '#cbd5e1', fontSize: '0.8rem' }}>{datasetDetails.dataset_id}</div>
                                                </div>
                                            </div>

                                            <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                                <Layers size={18} color="#8b5cf6" /> Source Runs
                                            </h3>
                                            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                                                {datasetDetails.sources.map((src, i) => (
                                                    <div key={i} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: '#1e293b', padding: '0.75rem', borderRadius: '6px', border: '1px solid #334155' }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                                                            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e' }}></div>
                                                            <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{src.symbol}</span>
                                                            <span style={{ fontSize: '0.75rem', background: '#334155', padding: '2px 6px', borderRadius: '4px' }}>{src.timeframe || 'N/A'}</span>
                                                        </div>
                                                        <span style={{ fontFamily: 'monospace', fontSize: '0.8rem', color: '#64748b' }}>{src.run_id}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    ) : (
                                        <DataExplorer dataset={datasetDetails} onUpdate={fetchDatasets} />
                                    )}
                                </div>
                            </>
                        ) : (
                            <div style={{ height: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
                                <Database size={48} style={{ opacity: 0.2, marginBottom: '1rem' }} />
                                <p>Select a dataset to view details</p>
                            </div>
                        )}
                    </div>
                </div>
            ) : (
                /* CREATE MODE */
                <div className="card" style={{ height: 'calc(100vh - 180px)', display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
                    <div style={{ padding: '1.5rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#1e293b' }}>
                        <h3 style={{ margin: 0 }}>Create New Dataset</h3>
                        <button onClick={() => setView('list')} style={{ background: 'none', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                            <X size={24} />
                        </button>
                    </div>

                    <div style={{ flex: 1, padding: '2rem', overflowY: 'auto' }}>
                        <div style={{ maxWidth: '800px', margin: '0 auto' }}>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem', marginBottom: '2rem' }}>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', color: '#cbd5e1' }}>Dataset Name</label>
                                    <input
                                        type="text"
                                        value={newName}
                                        onChange={e => setNewName(e.target.value)}
                                        placeholder="e.g. Golden Set BTC 2024"
                                        style={{ width: '100%', padding: '0.75rem', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
                                    />
                                </div>
                                <div>
                                    <label style={{ display: 'block', marginBottom: '0.5rem', color: '#cbd5e1' }}>Description</label>
                                    <input
                                        type="text"
                                        value={newDesc}
                                        onChange={e => setNewDesc(e.target.value)}
                                        placeholder="Optional description..."
                                        style={{ width: '100%', padding: '0.75rem', background: '#0f172a', border: '1px solid #334155', borderRadius: '6px', color: '#fff' }}
                                    />
                                </div>
                            </div>

                            <h3 style={{ fontSize: '1.1rem', marginBottom: '1rem', color: '#e2e8f0' }}>Select Source Runs</h3>
                            <div style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '8px', maxHeight: '400px', overflowY: 'auto' }}>
                                {runs.map(run => {
                                    const isSelected = selectedRuns.includes(run.run_id);
                                    return (
                                        <div
                                            key={run.run_id}
                                            onClick={() => toggleRunSelection(run.run_id)}
                                            style={{
                                                padding: '1rem',
                                                borderBottom: '1px solid #1e293b',
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '1rem',
                                                cursor: 'pointer',
                                                background: isSelected ? 'rgba(139, 92, 246, 0.1)' : 'transparent'
                                            }}
                                        >
                                            <div style={{
                                                width: '20px', height: '20px', borderRadius: '4px', border: isSelected ? 'none' : '2px solid #475569',
                                                background: isSelected ? '#8b5cf6' : 'transparent',
                                                display: 'flex', alignItems: 'center', justifyContent: 'center'
                                            }}>
                                                {isSelected && <Check size={14} color="white" />}
                                            </div>
                                            <div style={{ flex: 1 }}>
                                                <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                                                    <span style={{ fontWeight: 600, color: '#f1f5f9' }}>[{run.strategy_name}]</span>
                                                    <span style={{ color: '#cbd5e1' }}>{run.instance_name}</span>
                                                </div>
                                                <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem', display: 'flex', gap: '1rem' }}>
                                                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}><Calendar size={12} /> {new Date(run.start_time).toLocaleString()}</span>
                                                    <span style={{ fontFamily: 'monospace' }}>{run.symbol} {run.timeframe}</span>
                                                </div>
                                            </div>
                                            <div>
                                                <span style={{ fontSize: '0.75rem', padding: '2px 8px', borderRadius: '10px', background: run.status === 'COMPLETED' ? '#064e3b' : '#334155', color: run.status === 'COMPLETED' ? '#34d399' : '#94a3b8' }}>
                                                    {run.status}
                                                </span>
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        </div>
                    </div>

                    <div style={{ padding: '1.5rem', borderTop: '1px solid #334155', background: '#1e293b', display: 'flex', justifyContent: 'flex-end', gap: '1rem' }}>
                        <button
                            onClick={() => setView('list')}
                            style={{ padding: '0.75rem 1.5rem', background: 'transparent', color: '#94a3b8', border: 'none', cursor: 'pointer' }}
                        >
                            Cancel
                        </button>
                        <button
                            onClick={handleCreateDataset}
                            disabled={!newName || selectedRuns.length === 0}
                            style={{
                                padding: '0.75rem 2rem',
                                background: (!newName || selectedRuns.length === 0) ? '#475569' : '#8b5cf6',
                                color: 'white',
                                border: 'none',
                                borderRadius: '6px',
                                fontWeight: 600,
                                cursor: (!newName || selectedRuns.length === 0) ? 'not-allowed' : 'pointer',
                                display: 'flex', alignItems: 'center', gap: '0.5rem'
                            }}
                        >
                            <Check size={18} /> Create Dataset
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

// --- DATA EXPLORER SUB-COMPONENT ---

const DataExplorer = ({ dataset, onUpdate }) => {
    const [columns, setColumns] = useState([]);
    const [data, setData] = useState([]);
    const [loading, setLoading] = useState(false);

    // Manage local config state for toggling
    const [activeColumns, setActiveColumns] = useState(dataset.feature_config || []);
    const [menuOpen, setMenuOpen] = useState(false);
    const menuRef = useRef(null);

    // Helpers for type inference
    const getColumnType = (col) => {
        if (col.includes('ts') || col.includes('time')) return 'date';
        if (['open', 'high', 'low', 'close', 'volume'].includes(col.toLowerCase())) return 'number';
        // default fallback check based on first row of data
        if (data.length > 0) {
            const val = data[0][col];
            if (typeof val === 'number') return 'number';
        }
        return 'text';
    };

    const getIconForType = (type) => {
        switch (type) {
            case 'number': return <Hash size={12} className="text-blue-400" />;
            case 'date': return <Calendar size={12} className="text-green-400" />;
            default: return <Type size={12} className="text-slate-400" />;
        }
    };

    useEffect(() => {
        loadPreview();
    }, [dataset.dataset_id]);

    useEffect(() => {
        setActiveColumns(dataset.feature_config || []);
    }, [dataset.feature_config]);

    // Close menu on click outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (menuRef.current && !menuRef.current.contains(event.target)) {
                setMenuOpen(false);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);


    const loadPreview = async () => {
        setLoading(true);
        try {
            const res = await fetch(`/api/datasets/${dataset.dataset_id}/preview`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ limit: 50 })
            });
            if (res.ok) {
                const json = await res.json();
                setColumns(json.columns || []);
                setData(json.data || []);

                // If no config set yet, default to all columns
                if (!dataset.feature_config || dataset.feature_config.length === 0) {
                    setActiveColumns(json.columns || []);
                }
            }
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    const toggleColumn = (col) => {
        if (activeColumns.includes(col)) {
            setActiveColumns(activeColumns.filter(c => c !== col));
        } else {
            setActiveColumns([...activeColumns, col]);
        }
    };

    const handleSaveSchema = async () => {
        try {
            const res = await fetch(`/api/datasets/${dataset.dataset_id}`, {
                method: 'PATCH',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ feature_config: activeColumns })
            });
            if (res.ok) {
                alert("Schema updated!");
                onUpdate(); // Refresh parent list
            }
        } catch (e) {
            console.error(e);
        }
    };

    if (loading) return <div className="text-slate-500 p-4">Loading preview...</div>;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
            {/* Toolbar */}
            <div style={{ paddingBottom: '1rem', marginBottom: '1rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <div>
                        <h3 style={{ fontSize: '0.9rem', color: '#e2e8f0', margin: 0 }}>Data Preview</h3>
                        <p style={{ fontSize: '0.75rem', color: '#64748b', margin: 0 }}>Showing first 50 rows.</p>
                    </div>

                    {/* Columns Dropdown Manager */}
                    <div style={{ position: 'relative' }} ref={menuRef}>
                        <button
                            onClick={() => setMenuOpen(!menuOpen)}
                            style={{
                                display: 'flex', alignItems: 'center', gap: '0.5rem',
                                padding: '0.4rem 0.8rem', background: '#1e293b', border: '1px solid #334155', borderRadius: '6px', color: '#cbd5e1', fontSize: '0.8rem', cursor: 'pointer'
                            }}
                        >
                            <Layers size={14} /> Manage Columns <ChevronDown size={14} />
                        </button>

                        {menuOpen && (
                            <div style={{
                                position: 'absolute', top: '100%', left: 0, marginTop: '4px',
                                background: '#1e293b', border: '1px solid #334155', borderRadius: '6px',
                                padding: '0.5rem', width: '250px', maxHeight: '300px', overflowY: 'auto', zIndex: 50,
                                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.5)'
                            }}>
                                <div style={{ fontSize: '0.75rem', fontWeight: 600, color: '#94a3b8', marginBottom: '0.5rem' }}>VISIBLE COLUMNS</div>
                                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                                    {columns.map(col => (
                                        <div
                                            key={col}
                                            onClick={() => toggleColumn(col)}
                                            style={{
                                                display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.25rem 0.5rem', borderRadius: '4px',
                                                cursor: 'pointer',
                                                background: activeColumns.includes(col) ? 'rgba(139, 92, 246, 0.1)' : 'transparent',
                                                color: activeColumns.includes(col) ? '#e2e8f0' : '#64748b'
                                            }}
                                            className="hover:bg-slate-700/50"
                                        >
                                            <div style={{
                                                width: '14px', height: '14px', borderRadius: '3px', border: '1px solid #475569',
                                                background: activeColumns.includes(col) ? '#8b5cf6' : 'transparent', border: activeColumns.includes(col) ? 'none' : '1px solid #475569',
                                                display: 'flex', alignItems: 'center', justifyContent: 'center'
                                            }}>
                                                {activeColumns.includes(col) && <Check size={10} color="white" />}
                                            </div>
                                            <span style={{ fontSize: '0.8rem' }}>{col}</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
                <button
                    onClick={handleSaveSchema}
                    style={{
                        background: '#3b82f6', color: 'white', border: 'none', padding: '0.5rem 1rem', borderRadius: '6px', fontSize: '0.8rem', cursor: 'pointer'
                    }}
                >
                    Save Schema
                </button>
            </div>

            {/* Table Grid */}
            <div style={{ flex: 1, overflow: 'auto', border: '1px solid #334155', borderRadius: '6px', background: '#0f172a' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.8rem', textAlign: 'left' }}>
                    <thead style={{ position: 'sticky', top: 0, background: '#1e293b', zIndex: 10 }}>
                        <tr>
                            {activeColumns.map(col => (
                                <th
                                    key={col}
                                    className="group" // For hover effect
                                    style={{ padding: '0.6rem 0.8rem', borderBottom: '1px solid #334155', color: '#cbd5e1', whiteSpace: 'nowrap', verticalAlign: 'middle' }}
                                >
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '8px' }}>
                                        <span style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                            {getIconForType(getColumnType(col))}
                                            {col}
                                        </span>

                                        {/* Hide Button (Visible on Hover) */}
                                        <button
                                            onClick={(e) => { e.stopPropagation(); toggleColumn(col); }}
                                            title="Hide Column"
                                            className="opacity-0 group-hover:opacity-100 transition-opacity"
                                            style={{ background: 'transparent', border: 'none', cursor: 'pointer', color: '#64748b' }}
                                        >
                                            <EyeOff size={14} className="hover:text-red-400" />
                                        </button>
                                    </div>
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((row, i) => (
                            <tr key={i} style={{ borderBottom: '1px solid #1e293b' }} className="hover:bg-slate-800/30">
                                {activeColumns.map(col => (
                                    <td key={col} style={{ padding: '0.4rem 0.8rem', color: '#94a3b8', fontFamily: 'monospace' }}>
                                        {typeof row[col] === 'number' ? row[col].toFixed(5) : row[col]}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};

export default Datasets;
