import React, { useEffect, useMemo, useRef, useState, useCallback } from 'react'
import { Copy, Database, RefreshCw, Search, Plus, X, Layers, Activity, HardDrive, Eye, UploadCloud, FileText, CheckCircle, AlertTriangle, ArrowRight, Settings } from 'lucide-react'
import axios from 'axios'

const formatDate = (value) => {
    if (!value) return '—'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return '—'
    return date.toLocaleString('it-IT', {
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit'
    })
}

const buildSourceLabel = (source) => {
    if (!source) return 'Fonte anonima'
    // If it's a file upload
    if (source.source === 'file_upload') {
        return `File: ${source.filename || 'unknown'} (${source.format})`
    }
    const parts = []
    if (source.symbol) parts.push(source.symbol)
    if (source.timeframe) parts.push(source.timeframe)
    if (source.venue) parts.push(source.venue)
    if (source.run_id) parts.push(`run ${source.run_id.slice(0, 6)}`)
    return parts.length ? parts.join(' • ') : 'Fonte anonima'
}

const Datasets = () => {
    const [datasets, setDatasets] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [searchTerm, setSearchTerm] = useState('')
    const [selectedId, setSelectedId] = useState(null)
    const [copiedId, setCopiedId] = useState(null)
    const copyTimeoutRef = useRef(null)

    // Creation / Import State
    const [isCreateOpen, setIsCreateOpen] = useState(false)
    const [importMode, setImportMode] = useState('manual') // 'manual' | 'file'
    const [dragActive, setDragActive] = useState(false)

    // File Import State
    const [importedFile, setImportedFile] = useState(null)
    const [previewData, setPreviewData] = useState(null)
    const [importStep, setImportStep] = useState(0) // 0: File Drop, 1.5: Table Select, 1: Config, 2: Uploading
    const [selectedColumns, setSelectedColumns] = useState({})

    // SQLite Specific
    const [dbTables, setDbTables] = useState([])
    const [selectedTable, setSelectedTable] = useState(null)


    // Form State
    const [newName, setNewName] = useState('')
    const [newDesc, setNewDesc] = useState('')
    const [newSymbol, setNewSymbol] = useState('BTCUSDT')
    const [newTimeframe, setNewTimeframe] = useState('1m')

    const [creating, setCreating] = useState(false)
    const [materializing, setMaterializing] = useState(false)
    const [samples, setSamples] = useState([])
    const [samplesLoading, setSamplesLoading] = useState(false)
    const [showSamples, setShowSamples] = useState(false)

    // --- Drag & Drop Handlers ---
    const handleDrag = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true)
        } else if (e.type === "dragleave") {
            setDragActive(false)
        }
    }, [])

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileSelect(e.dataTransfer.files[0])
        }
    }, [])

    const fetchPreview = async (file, config = {}) => {
        const formData = new FormData()
        formData.append('file', file)
        if (Object.keys(config).length) {
            formData.append('config', JSON.stringify(config))
        }

        try {
            const res = await axios.post('http://127.0.0.1:8000/api/datasets/preview-upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            return res.data
        } catch (err) {
            throw err
        }
    }

    const handleFileSelect = async (file) => {
        setImportedFile(file)
        setNewName(file.name.split('.')[0].replace(/[^a-zA-Z0-9-_]/g, '_')) // Sanitize name
        setImportMode('file')
        setIsCreateOpen(true)

        // Reset states
        setPreviewData(null)
        setDbTables([])
        setSelectedTable(null)

        try {
            const data = await fetchPreview(file)

            // Check if we need to select a table (SQLite)
            if (data.tables && data.tables.length > 0) {
                setDbTables(data.tables)
                setImportStep(1.5) // Intermediate step: Table Select
                return
            }

            processPreviewData(data)

        } catch (err) {
            console.error("Preview failed", err)
            alert("Failed to preview file: " + (err.response?.data?.detail || err.message))
            setImportedFile(null)
            setImportStep(0)
        }
    }

    const handleTableSelect = async (table) => {
        if (!importedFile) return
        setSelectedTable(table)
        setImportStep(Number(1.5)) // Keep loading state if needed, but we just fetch

        try {
            const data = await fetchPreview(importedFile, { table_name: table })
            processPreviewData(data)
        } catch (err) {
            console.error("Table preview failed", err)
            alert("Failed to load table: " + (err.response?.data?.detail || err.message))
        }
    }

    const processPreviewData = (data) => {
        setPreviewData(data)
        setImportStep(1) // Go to Config

        // Auto-select all columns except 'timestamp_utc'
        const initialSelection = {}
        data.columns.forEach(c => {
            if (c !== 'timestamp_utc') {
                initialSelection[c] = true
            }
        })
        setSelectedColumns(initialSelection)
    }

    const submitCreateOrUpload = async () => {
        setCreating(true)
        try {
            if (importMode === 'manual') {
                // ... Existing Manual Creation Logic ...
                const payload = {
                    name: newName,
                    description: newDesc,
                    sources_json: [{
                        symbol: newSymbol,
                        timeframe: newTimeframe,
                        venue: 'Binance',
                        provider: 'Quantower'
                    }],
                    feature_config_json: ["open", "high", "low", "close", "volume"]
                }

                await axios.post('http://127.0.0.1:8000/api/datasets/', payload)

            } else {
                // ... File Upload Logic ...
                if (!importedFile) return

                const feature_columns = Object.keys(selectedColumns).filter(k => selectedColumns[k])

                const config = {
                    feature_columns: feature_columns,
                    timestamp_column: previewData?.columns.includes('timestamp_utc') ? 'timestamp_utc' : 'time'
                }

                // If table was selected, pass it
                if (selectedTable) {
                    config.table_name = selectedTable
                }

                const formData = new FormData()
                formData.append('name', newName)
                formData.append('description', newDesc)
                formData.append('file', importedFile)
                formData.append('config', JSON.stringify(config))

                await axios.post('http://127.0.0.1:8000/api/datasets/upload-file-create', formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                })
            }

            await fetchDatasets()
            setIsCreateOpen(false)
            setImportedFile(null)
            setPreviewData(null)
            setImportStep(0)
        } catch (e) {
            console.error(e)
            alert("Error: " + (e.response?.data?.detail || e.message))
        } finally {
            setCreating(false)
        }
    }

    // ... Existing Handlers ...

    const handleMaterialize = async (id) => {
        if (!confirm("Materialize data from Market Series?")) return
        setMaterializing(true)
        try {
            const res = await axios.post(`http://127.0.0.1:8000/api/datasets/${id}/materialize`)
            alert(`Completed: ${res.data.materialized_count} samples created.`)
        } catch (e) {
            alert("Error: " + (e.response?.data?.detail || e.message))
        } finally {
            setMaterializing(false)
        }
    }

    const fetchSamples = async (id) => {
        setSamplesLoading(true)
        setSamples([])
        setShowSamples(true)
        try {
            const res = await axios.get(`http://127.0.0.1:8000/api/datasets/${id}/samples?limit=20`)
            setSamples(res.data)
        } catch (e) {
            console.error(e)
        } finally {
            setSamplesLoading(false)
        }
    }

    const fetchDatasets = async () => {
        setLoading(true)
        setError(null)
        try {
            const response = await axios.get('http://127.0.0.1:8000/api/datasets/')
            const payload = response.data
            setDatasets(payload)
            setSelectedId((current) => {
                if (current && payload.some((entry) => entry.dataset_id === current)) {
                    return current
                }
                return payload[0]?.dataset_id ?? null
            })
        } catch (err) {
            setError(err.message || 'Error loading datasets')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchDatasets()
    }, [])

    const filteredDatasets = useMemo(() => {
        const term = searchTerm.trim().toLowerCase()
        if (!term) return datasets
        return datasets.filter((dataset) => {
            const haystack = `${dataset.name ?? ''} ${dataset.dataset_id ?? ''} ${dataset.description ?? ''}`.toLowerCase()
            return haystack.includes(term)
        })
    }, [datasets, searchTerm])

    useEffect(() => {
        if (!datasets.length) return
        if (!filteredDatasets.length) {
            setSelectedId(null)
            return
        }
        if (!selectedId || !filteredDatasets.some(d => d.dataset_id === selectedId)) {
            setSelectedId(filteredDatasets[0].dataset_id)
        }
    }, [filteredDatasets, selectedId])

    useEffect(() => {
        setShowSamples(false)
        setSamples([])
    }, [selectedId])

    const handleCopyId = async (datasetId) => {
        if (!navigator.clipboard) return
        try {
            await navigator.clipboard.writeText(datasetId)
            setCopiedId(datasetId)
            if (copyTimeoutRef.current) clearTimeout(copyTimeoutRef.current)
            copyTimeoutRef.current = setTimeout(() => setCopiedId(null), 1700)
        } catch (copyError) {
            console.warn('Copy failed', copyError)
        }
    }

    const datasetStats = useMemo(() => {
        let totalSources = 0
        let datasetsWithSources = 0
        let totalFeatures = 0
        let newest = null
        datasets.forEach((dataset) => {
            const sources = dataset.sources_json ?? []
            if (sources.length) {
                datasetsWithSources += 1
                totalSources += sources.length
            }
            totalFeatures += (dataset.feature_config_json?.length ?? 0)
            if (!newest || new Date(dataset.created_utc).getTime() > new Date(newest.created_utc).getTime()) {
                newest = dataset
            }
        })
        return { total: datasets.length, totalSources, datasetsWithSources, totalFeatures, newest }
    }, [datasets])

    const selectedDataset = filteredDatasets.find((d) => d.dataset_id === selectedId) ?? null
    const featuresToShow = selectedDataset?.feature_config_json ?? []
    const visibleFeatures = featuresToShow.slice(0, 10)
    const moreFeatures = featuresToShow.length - visibleFeatures.length

    // Check if newName exists for Upsert warning
    const nameExists = useMemo(() => {
        if (!newName) return false
        return datasets.some(d => d.name.toLowerCase() === newName.toLowerCase() && d.dataset_id !== selectedId)
    }, [newName, datasets])

    return (
        <section
            className="flex flex-col gap-6 h-full font-sans text-slate-100 relative"
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
        >
            {/* Full Screen Drag Overlay */}
            {dragActive && (
                <div className="absolute inset-0 z-50 bg-slate-900/90 backdrop-blur-md flex flex-col items-center justify-center animate-in fade-in duration-200 border-4 border-dashed border-accent rounded-xl m-4">
                    <UploadCloud size={64} className="text-accent animate-bounce mb-4" />
                    <h2 className="text-2xl font-bold text-white">Drop to Import Dataset</h2>
                    <p className="text-slate-400 mt-2">Release file to start the ETL process</p>
                </div>
            )}

            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div>
                    <div className="flex items-center gap-2 text-xs font-bold text-accent tracking-wider uppercase mb-1">
                        <Layers size={14} /> Assets ML · Dataset
                    </div>
                    <h1 className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                        Dataset Management
                    </h1>
                    <p className="text-slate-400 mt-1 max-w-2xl">
                        Filter, update, and inspect datasets. Drag & drop files to upsert data.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={() => { setIsCreateOpen(true); setImportMode('manual'); }}
                        className="btn-primary shadow-lg shadow-blue-500/20"
                    >
                        <Plus size={18} />
                        <span>New Dataset</span>
                    </button>
                    <button
                        type="button"
                        onClick={fetchDatasets}
                        disabled={loading}
                        className="btn-secondary bg-slate-800/50 backdrop-blur-sm border-slate-700/50 hover:bg-slate-700/50"
                    >
                        <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                    </button>
                </div>
            </div>

            {/* Global Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="card bg-gradient-to-br from-slate-800/40 to-slate-900/40 border-slate-700/50 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity"><Database size={64} /></div>
                    <p className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Total Datasets</p>
                    <p className="text-3xl font-bold text-white">{datasetStats.total}</p>
                    <p className="text-xs text-slate-400 mt-1">Latest: <span className="text-slate-200">{datasetStats.newest?.name ?? '—'}</span></p>
                </div>
                {/* ... other stats ... */}
                <div className="card bg-gradient-to-br from-slate-800/40 to-slate-900/40 border-slate-700/50 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity"><FileText size={64} /></div>
                    <p className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Sources</p>
                    <p className="text-3xl font-bold text-white">{datasetStats.totalSources}</p>
                    <p className="text-xs text-slate-400 mt-1">{datasetStats.datasetsWithSources} datasets with data</p>
                </div>
                <div className="card bg-gradient-to-br from-slate-800/40 to-slate-900/40 border-slate-700/50 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity"><Activity size={64} /></div>
                    <p className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Total Features</p>
                    <p className="text-3xl font-bold text-white">{datasetStats.totalFeatures}</p>
                    <p className="text-xs text-slate-400 mt-1">Learned properties</p>
                </div>
            </div>

            {/* Main Content Grid */}
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
                {/* Left: Table List */}
                <div className="lg:col-span-2 flex flex-col min-h-0 card p-0 border-slate-700/50 overflow-hidden bg-slate-900/30">
                    <div className="p-4 border-b border-slate-700/50 flex items-center justify-between gap-4 bg-slate-900/20">
                        <div className="relative flex-1 max-w-md">
                            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                            <input
                                type="search"
                                placeholder="Search datasets..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg py-2 pl-9 pr-4 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all"
                            />
                        </div>
                        <span className="text-xs font-mono text-slate-500">{loading ? 'Loading...' : `${filteredDatasets.length} items`}</span>
                    </div>

                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                        <table className="w-full text-left border-collapse">
                            <thead className="sticky top-0 bg-slate-900/95 backdrop-blur-md z-10 border-b border-slate-700/50 shadow-sm">
                                <tr>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[40%]">Dataset</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Source info</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Vars</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Created</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/50">
                                {filteredDatasets.map((dataset) => {
                                    const sourcesCount = dataset.sources_json?.length ?? 0
                                    const isSelected = selectedId === dataset.dataset_id
                                    return (
                                        <tr
                                            key={dataset.dataset_id}
                                            onClick={() => setSelectedId(dataset.dataset_id)}
                                            className={`group cursor-pointer transition-colors duration-150 ${isSelected ? 'bg-accent/5 border-l-2 border-accent' : 'hover:bg-slate-800/30 border-l-2 border-transparent'}`}
                                        >
                                            <td className="py-3 px-4">
                                                <div className="flex items-start gap-3">
                                                    <div className={`mt-1 p-1.5 rounded-md ${isSelected ? 'bg-accent/20 text-accent' : 'bg-slate-800 text-slate-400 group-hover:text-slate-200'}`}>
                                                        <Database size={16} />
                                                    </div>
                                                    <div>
                                                        <div className={`font-semibold text-sm ${isSelected ? 'text-accent' : 'text-slate-200 group-hover:text-white'}`}>{dataset.name}</div>
                                                        <div className="flex items-center gap-1.5 mt-0.5">
                                                            <code className="text-[10px] text-slate-500 font-mono bg-slate-900/50 px-1 rounded border border-slate-800">{dataset.dataset_id.slice(0, 8)}...</code>
                                                            <button onClick={(e) => { e.stopPropagation(); handleCopyId(dataset.dataset_id) }} className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 text-slate-500 hover:text-accent" title="Copy ID">
                                                                <Copy size={10} />
                                                            </button>
                                                            {copiedId === dataset.dataset_id && <span className="text-[10px] text-emerald-400 animate-fade-in">Copied!</span>}
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="py-3 px-4">
                                                <div className="text-sm text-slate-300">{sourcesCount} source{sourcesCount !== 1 && 's'}</div>
                                                <div className="text-xs text-slate-500 truncate max-w-[150px]">{buildSourceLabel(dataset.sources_json?.[0])}</div>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                                <div className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700/50">
                                                    {dataset.feature_config_json?.length ?? 0}
                                                </div>
                                            </td>
                                            <td className="py-3 px-4 text-right text-xs text-slate-400 font-mono">{formatDate(dataset.created_utc)}</td>
                                        </tr>
                                    )
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Right: Details Panel */}
                <div className="lg:col-span-1 min-h-0 flex flex-col">
                    <div className="card h-full flex flex-col p-5 bg-slate-800/40 backdrop-blur-xl border-slate-700/50 overflow-hidden sticky top-4">
                        <div className="mb-6 pb-4 border-b border-slate-700/50">
                            <p className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Selected Details</p>
                            <h3 className="text-xl font-bold text-white leading-tight">{selectedDataset?.name ?? 'No Selection'}</h3>
                            {selectedDataset && (
                                <div className="mt-2 flex items-center gap-2">
                                    <code className="text-xs bg-black/30 text-accent px-1.5 py-0.5 rounded font-mono border border-accent/20">{selectedDataset.dataset_id}</code>
                                </div>
                            )}
                        </div>

                        {selectedDataset ? (
                            <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-6 pr-2">
                                {/* Description */}
                                {selectedDataset.description && (
                                    <div>
                                        <h4 className="text-xs font-semibold text-slate-400 uppercase mb-2">Description</h4>
                                        <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/30 p-3 rounded-lg border border-slate-700/30">{selectedDataset.description}</p>
                                    </div>
                                )}

                                <div>
                                    <h4 className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2"><Database size={12} /> Sources</h4>
                                    {selectedDataset.sources_json?.length ? (
                                        <ul className="space-y-2">
                                            {selectedDataset.sources_json.map((source, index) => (
                                                <li key={index} className="text-sm bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 group hover:border-accent/30 transition-colors">
                                                    <div className="font-semibold text-slate-200">{buildSourceLabel(source)}</div>
                                                    {source.uploaded_at && <div className="text-xs text-slate-500 mt-1">Uploaded: {formatDate(source.uploaded_at)}</div>}
                                                </li>
                                            ))}
                                        </ul>
                                    ) : <p className="text-sm text-slate-500 italic">No sources registered.</p>}
                                </div>

                                <div>
                                    <h4 className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2"><Activity size={12} /> Features</h4>
                                    <div className="flex flex-wrap gap-1.5">
                                        {visibleFeatures.length ? (
                                            <>
                                                {visibleFeatures.map((f, i) => (
                                                    <span key={i} className="px-2 py-1 text-xs rounded bg-slate-700/50 text-slate-300 border border-slate-600/50">{f}</span>
                                                ))}
                                                {moreFeatures > 0 && <span className="px-2 py-1 text-xs rounded bg-slate-800 text-slate-500 border border-slate-700 border-dashed">+{moreFeatures} more</span>}
                                            </>
                                        ) : <p className="text-sm text-slate-500 italic">No features configured.</p>}
                                    </div>
                                </div>

                                <div className="grid grid-cols-2 gap-3 pt-4 mt-auto border-t border-slate-700/50">
                                    <button
                                        onClick={() => handleMaterialize(selectedId)}
                                        disabled={materializing || selectedDataset?.sources_json?.some(s => s.source === 'file_upload')}
                                        className="btn-secondary justify-center text-xs py-2 bg-indigo-500/10 text-indigo-300 border-indigo-500/30 hover:bg-indigo-500/20 disabled:opacity-50 disabled:cursor-not-allowed"
                                        title={selectedDataset?.sources_json?.some(s => s.source === 'file_upload') ? "Dataset imported from file is already materialized" : "Materialize data from Market Series"}
                                    >
                                        <HardDrive size={14} className={materializing ? 'animate-spin' : ''} />
                                        <span>{selectedDataset?.sources_json?.some(s => s.source === 'file_upload') ? 'Auto-Materialized' : 'Materialize'}</span>
                                    </button>
                                    <button onClick={() => fetchSamples(selectedId)} disabled={samplesLoading} className="btn-secondary justify-center text-xs py-2">
                                        <Eye size={14} className={samplesLoading ? 'animate-spin' : ''} /> <span>Preview</span>
                                    </button>
                                </div>

                                {showSamples && (
                                    <div className="mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-xs font-semibold text-slate-400">Data Preview (20 rows)</span>
                                            <button onClick={() => setShowSamples(false)} className="text-xs text-slate-500 hover:text-white"><X size={12} /></button>
                                        </div>
                                        {samples.length > 0 ? (
                                            <div className="bg-slate-950 rounded-lg border border-slate-800 overflow-x-auto p-2">
                                                <table className="w-full text-[10px] font-mono whitespace-nowrap">
                                                    <thead>
                                                        <tr className="text-slate-500 text-left">
                                                            <th className="p-1.5 pb-2">Time</th>
                                                            {Object.keys(samples[0].features_json).slice(0, 4).map(k => <th key={k} className="p-1.5 pb-2 text-right">{k}</th>)}
                                                        </tr>
                                                    </thead>
                                                    <tbody className="divide-y divide-slate-800">
                                                        {samples.map((s) => (
                                                            <tr key={s.sample_id}>
                                                                <td className="p-1.5 text-slate-600">{formatDate(s.timestamp_utc).split(',')[1]}</td>
                                                                {Object.values(s.features_json).slice(0, 4).map((v, i) => (
                                                                    <td key={i} className="p-1.5 text-right text-slate-300">{typeof v === 'number' ? v.toFixed(2) : v}</td>
                                                                ))}
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        ) : <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800 text-center text-xs text-slate-500">No data.</div>}
                                    </div>
                                )}
                            </div>
                        ) : <div className="flex-1 flex flex-col items-center justify-center text-center opacity-40"><Database size={48} className="mb-4 text-slate-600" /><p className="text-sm text-slate-400 max-w-[200px]">Select a dataset.</p></div>}
                    </div>
                </div>
            </div>

            {/* Create / Import Modal */}
            {isCreateOpen && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
                    <div className="card w-full max-w-2xl p-0 bg-slate-900 border-slate-700 shadow-2xl scale-100 animate-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
                        {/* Header */}
                        <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-800/30">
                            <div>
                                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                    {importMode === 'manual' ? <Plus size={18} className="text-accent" /> : <UploadCloud size={18} className="text-accent" />}
                                    {importMode === 'manual' ? 'Create Empty Dataset' : 'Import Dataset'}
                                </h2>
                                <p className="text-xs text-slate-500">
                                    {importMode === 'manual' ? 'Define metadata manually' : 'Configure imported data'}
                                </p>
                            </div>
                            <button onClick={() => setIsCreateOpen(false)} className="text-slate-500 hover:text-white transition-colors"><X size={20} /></button>
                        </div>

                        {/* Body */}
                        <div className="p-6 flex-1 overflow-y-auto custom-scrollbar space-y-6">

                            {/* Mode Toggle (if simple) - Actually we use drag drop or button to switch. */}

                            {/* Step 1.5: Table Selection (SQlite) */}
                            {importMode === 'file' && importStep === 1.5 && (
                                <div className="space-y-4">
                                    <div className="bg-blue-500/10 border border-blue-500/20 p-4 rounded-lg flex items-center gap-3">
                                        <Database size={24} className="text-blue-400" />
                                        <div>
                                            <h3 className="text-sm font-bold text-white">Database Detected</h3>
                                            <p className="text-xs text-slate-400">Select a table to import from <b>{importedFile?.name}</b></p>
                                        </div>
                                    </div>
                                    <div className="grid grid-cols-1 gap-2 max-h-[300px] overflow-y-auto custom-scrollbar">
                                        {dbTables.map(table => (
                                            <button
                                                key={table}
                                                onClick={() => handleTableSelect(table)}
                                                className="flex items-center justify-between p-3 rounded-lg bg-slate-950/50 border border-slate-800 hover:border-accent hover:bg-slate-900 transition-all text-left group"
                                            >
                                                <span className="text-sm text-slate-300 font-mono group-hover:text-white">{table}</span>
                                                <ArrowRight size={14} className="text-slate-600 group-hover:text-accent transform group-hover:translate-x-1 transition-transform" />
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Step 1: Config & Preview */}
                            {importMode === 'file' && previewData && importStep === 1 && (
                                <div className="bg-slate-950 rounded-lg border border-slate-800 p-4 mb-4">
                                    <div className="flex items-center gap-3 mb-4">
                                        <div className="bg-blue-500/20 p-2 rounded-lg text-blue-400">
                                            <FileText size={24} />
                                        </div>
                                        <div className="flex-1">
                                            <div className="text-sm font-bold text-white max-w-[300px] truncate" title={previewData.filename}>{previewData.filename}</div>
                                            <div className="text-xs text-slate-500">{previewData.total_columns} columns identified</div>
                                        </div>
                                        <div className="text-xs px-2 py-1 bg-green-500/10 text-green-400 rounded border border-green-500/20">
                                            Ready to Process
                                        </div>
                                    </div>

                                    {/* Column Selection */}
                                    <div>
                                        <h4 className="text-xs font-bold text-slate-400 uppercase mb-2 flex items-center gap-2">
                                            <Settings size={12} /> Map Features
                                        </h4>
                                        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                                            {previewData.columns.map(col => (
                                                <label key={col} className={`
                                                    flex items-center gap-2 p-2 rounded border text-xs cursor-pointer transition-colors select-none
                                                    ${selectedColumns[col] ? 'bg-accent/10 border-accent/30 text-white' : 'bg-slate-900 border-slate-800 text-slate-500 hover:bg-slate-800'}
                                                 `}>
                                                    <input
                                                        type="checkbox"
                                                        className="sr-only"
                                                        checked={!!selectedColumns[col]}
                                                        onChange={() => setSelectedColumns(prev => ({ ...prev, [col]: !prev[col] }))}
                                                    />
                                                    <div className={`w-3 h-3 rounded-full border flex items-center justify-center ${selectedColumns[col] ? 'bg-accent border-accent' : 'border-slate-600'}`}>
                                                        {selectedColumns[col] && <CheckCircle size={8} className="text-white" />}
                                                    </div>
                                                    <span className="truncate" title={col}>{col}</span>
                                                </label>
                                            ))}
                                        </div>
                                        <p className="text-[10px] text-slate-500 mt-2">Uncheck columns you want to exclude from the dataset.</p>
                                    </div>
                                </div>
                            )}

                            {/* Standard Form Fields */}
                            <div className="space-y-4">
                                <div className="form-group">
                                    <label className="text-sm font-medium text-slate-400 mb-1.5 block">Dataset Name <span className="text-red-400">*</span></label>
                                    <input
                                        type="text"
                                        value={newName}
                                        onChange={e => setNewName(e.target.value)}
                                        placeholder="e.g. BTC High Volatility"
                                        className="input-field bg-slate-950 border-slate-700 focus:border-accent w-full p-2 rounded"
                                    />
                                    {nameExists && (
                                        <div className="flex items-center gap-2 mt-2 text-amber-400 text-xs bg-amber-500/10 p-2 rounded border border-amber-500/20">
                                            <AlertTriangle size={12} />
                                            <span>Dataset exists. Data will be <b>Upserted</b> (appended) to existing set.</span>
                                        </div>
                                    )}
                                </div>

                                <div className="form-group">
                                    <label className="text-sm font-medium text-slate-400 mb-1.5 block">Description</label>
                                    <textarea
                                        value={newDesc}
                                        onChange={e => setNewDesc(e.target.value)}
                                        placeholder="Describe the dataset content..."
                                        className="input-field bg-slate-950 border-slate-700 focus:border-accent w-full p-2 rounded min-h-[80px]"
                                    />
                                </div>

                                {importMode === 'manual' && (
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="form-group">
                                            <label className="text-sm font-medium text-slate-400 mb-1.5 block">Symbol <span className="text-red-400">*</span></label>
                                            <input type="text" value={newSymbol} onChange={e => setNewSymbol(e.target.value)} className="input-field bg-slate-950 border-slate-700 focus:border-accent w-full p-2 rounded" />
                                        </div>
                                        <div className="form-group">
                                            <label className="text-sm font-medium text-slate-400 mb-1.5 block">Timeframe <span className="text-red-400">*</span></label>
                                            <select value={newTimeframe} onChange={e => setNewTimeframe(e.target.value)} className="input-field bg-slate-950 border-slate-700 focus:border-accent w-full p-2 rounded">
                                                {['1m', '5m', '15m', '1h', '4h', '1d'].map(tf => <option key={tf} value={tf}>{tf}</option>)}
                                            </select>
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Footer */}
                        <div className="p-5 border-t border-slate-800 flex justify-between items-center bg-slate-800/30 rounded-b-xl">
                            {importMode === 'file' ? (
                                <button className="text-xs text-slate-500 hover:text-white underline" onClick={() => { setImportedFile(null); setImportMode('manual'); }}>Switch to Manual</button>
                            ) : (
                                <div></div>
                            )}
                            <div className="flex gap-3">
                                <button onClick={() => setIsCreateOpen(false)} className="btn-secondary text-sm py-2 px-4 hover:bg-slate-800">Cancel</button>
                                <button
                                    onClick={submitCreateOrUpload}
                                    disabled={!newName || creating || (importMode === 'file' && !importedFile)}
                                    className="btn-primary text-sm py-2 px-6 shadow-lg shadow-accent/20 flex items-center gap-2"
                                >
                                    {creating ? <RefreshCw size={16} className="animate-spin" /> : (nameExists ? <RefreshCw size={16} /> : <Plus size={16} />)}
                                    <span>{creating ? 'Processing...' : (nameExists ? 'Upsert Dataset' : 'Create Dataset')}</span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </section>
    )
}

export default Datasets
