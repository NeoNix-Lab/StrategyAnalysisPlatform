import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Copy, Database, RefreshCw, Search, Plus, X, Layers, Activity, HardDrive, Eye } from 'lucide-react'

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

const formatBoundary = (value) => {
    if (!value) return null
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return null
    return date.toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
}

const buildSourceLabel = (source) => {
    if (!source) return 'Fonte anonima'
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

    // Creation State
    const [isCreateOpen, setIsCreateOpen] = useState(false)
    const [newName, setNewName] = useState('')
    const [newDesc, setNewDesc] = useState('')
    const [newSymbol, setNewSymbol] = useState('BTCUSDT')
    const [newTimeframe, setNewTimeframe] = useState('1m')
    const [creating, setCreating] = useState(false)
    const [materializing, setMaterializing] = useState(false)
    const [samples, setSamples] = useState([])
    const [samplesLoading, setSamplesLoading] = useState(false)
    const [showSamples, setShowSamples] = useState(false)

    const handleCreateWrapper = () => {
        setNewName('')
        setNewDesc('')
        setIsCreateOpen(true)
    }

    const submitCreate = async () => {
        if (!newName || !newSymbol || !newTimeframe) return
        setCreating(true)
        try {
            const payload = {
                name: newName,
                description: newDesc,
                sources_json: [{
                    symbol: newSymbol,
                    timeframe: newTimeframe,
                    venue: 'Binance',  // Default for now
                    provider: 'Quantower' // Default
                }],
                feature_config_json: ["open", "high", "low", "close", "volume"] // Default Features
            }

            const res = await fetch('/api/datasets/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            })

            if (res.ok) {
                await fetchDatasets()
                setIsCreateOpen(false)
            } else {
                alert("Errore durante la creazione del dataset")
            }
        } catch (e) {
            console.error(e)
            alert("Errore di rete")
        } finally {
            setCreating(false)
        }
    }

    const handleMaterialize = async (id) => {
        if (!confirm("Vuoi materializzare i dati da Market Series a campioni concreti?")) return
        setMaterializing(true)
        try {
            const res = await fetch(`/api/datasets/${id}/materialize`, { method: 'POST' })
            const data = await res.json()
            if (res.ok) {
                alert(`Materializzazione completata: ${data.materialized_count} campioni creati.`)
            } else {
                alert(`Errore: ${data.detail}`)
            }
        } catch (e) {
            console.error(e)
            alert("Errore di rete")
        } finally {
            setMaterializing(false)
        }
    }

    const fetchSamples = async (id) => {
        setSamplesLoading(true)
        setSamples([])
        setShowSamples(true)
        try {
            const res = await fetch(`/api/datasets/${id}/samples?limit=20`)
            if (res.ok) {
                const data = await res.json()
                setSamples(data)
            }
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
            const response = await fetch('/api/datasets')
            if (!response.ok) {
                throw new Error('Impossibile caricare i dataset')
            }
            const payload = await response.json()
            setDatasets(payload)
            setSelectedId((current) => {
                if (current && payload.some((entry) => entry.dataset_id === current)) {
                    return current
                }
                return payload[0]?.dataset_id ?? null
            })
        } catch (err) {
            setError(err.message || 'Errore sconosciuto durante il caricamento')
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchDatasets()
    }, [])

    const filteredDatasets = useMemo(() => {
        const term = searchTerm.trim().toLowerCase()
        if (!term) {
            return datasets
        }
        return datasets.filter((dataset) => {
            const haystack = `${dataset.name ?? ''} ${dataset.dataset_id ?? ''} ${dataset.description ?? ''}`.toLowerCase()
            return haystack.includes(term)
        })
    }, [datasets, searchTerm])

    useEffect(() => {
        if (!filteredDatasets.length) {
            setSelectedId(null)
            return
        }
        if (selectedId && filteredDatasets.some((dataset) => dataset.dataset_id === selectedId)) {
            return
        }
        setSelectedId(filteredDatasets[0].dataset_id)
    }, [filteredDatasets, selectedId])

    // Reset samples view when selection changes
    useEffect(() => {
        setShowSamples(false)
        setSamples([])
    }, [selectedId])

    useEffect(() => {
        return () => {
            if (copyTimeoutRef.current) {
                clearTimeout(copyTimeoutRef.current)
            }
        }
    }, [])

    const handleCopyId = async (datasetId) => {
        if (!navigator.clipboard) {
            return
        }
        try {
            await navigator.clipboard.writeText(datasetId)
            setCopiedId(datasetId)
            if (copyTimeoutRef.current) {
                clearTimeout(copyTimeoutRef.current)
            }
            copyTimeoutRef.current = setTimeout(() => {
                setCopiedId(null)
            }, 1700)
        } catch (copyError) {
            console.warn('Copia fallita', copyError)
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
            if (!newest) {
                newest = dataset
                return
            }
            const candidateTime = new Date(dataset.created_utc ?? 0).getTime()
            const currentTime = new Date(newest.created_utc ?? 0).getTime()
            if (candidateTime > currentTime) {
                newest = dataset
            }
        })

        return {
            total: datasets.length,
            totalSources,
            datasetsWithSources,
            totalFeatures,
            newest
        }
    }, [datasets])

    const selectedDataset =
        filteredDatasets.find((dataset) => dataset.dataset_id === selectedId) ??
        filteredDatasets[0] ??
        null

    const featuresToShow = selectedDataset?.feature_config_json ?? []
    const visibleFeatures = featuresToShow.slice(0, 10)
    const moreFeatures = featuresToShow.length - visibleFeatures.length

    return (
        <section className="flex flex-col gap-6 h-full font-sans text-slate-100">
            {/* Header */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div>
                    <div className="flex items-center gap-2 text-xs font-bold text-accent tracking-wider uppercase mb-1">
                        <Layers size={14} /> Assets ML · Dataset
                    </div>
                    <h1 className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                        Gestione set di dati
                    </h1>
                    <p className="text-slate-400 mt-1 max-w-2xl">
                        Filtra, aggiorna e ispeziona i dataset già registrati nel laboratorio quantitativo.
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    <button
                        type="button"
                        onClick={handleCreateWrapper}
                        className="btn-primary shadow-lg shadow-blue-500/20"
                    >
                        <Plus size={18} />
                        <span>Nuovo Dataset</span>
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
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Database size={64} />
                    </div>
                    <p className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Dataset registrati</p>
                    <p className="text-3xl font-bold text-white">{datasetStats.total}</p>
                    <p className="text-xs text-slate-400 mt-1">Ultimo: <span className="text-slate-200">{datasetStats.newest?.name ?? '—'}</span></p>
                </div>
                <div className="card bg-gradient-to-br from-slate-800/40 to-slate-900/40 border-slate-700/50 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Activity size={64} />
                    </div>
                    <p className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Fonti definite</p>
                    <p className="text-3xl font-bold text-white">{datasetStats.datasetsWithSources}</p>
                    <p className="text-xs text-slate-400 mt-1">{datasetStats.totalSources} fonti totali</p>
                </div>
                <div className="card bg-gradient-to-br from-slate-800/40 to-slate-900/40 border-slate-700/50 relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
                        <Layers size={64} />
                    </div>
                    <p className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Variabili</p>
                    <p className="text-3xl font-bold text-white">{datasetStats.totalFeatures}</p>
                    <p className="text-xs text-slate-400 mt-1">Configurazioni note</p>
                </div>
            </div>

            {/* Main Content Grid */}
            <div className="flex-1 grid grid-cols-1 lg:grid-cols-3 gap-6 min-h-0">
                {/* Left: Table List */}
                <div className="lg:col-span-2 flex flex-col min-h-0 card p-0 border-slate-700/50 overflow-hidden bg-slate-900/30">
                    {/* Toolbar */}
                    <div className="p-4 border-b border-slate-700/50 flex items-center justify-between gap-4 bg-slate-900/20">
                        <div className="relative flex-1 max-w-md">
                            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                            <input
                                type="search"
                                placeholder="Cerca..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg py-2 pl-9 pr-4 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all"
                            />
                        </div>
                        <span className="text-xs font-mono text-slate-500">
                            {loading ? 'Caricamento...' : `${filteredDatasets.length} items`}
                        </span>
                    </div>

                    {/* Table */}
                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                        <table className="w-full text-left border-collapse">
                            <thead className="sticky top-0 bg-slate-900/95 backdrop-blur-md z-10 border-b border-slate-700/50 shadow-sm">
                                <tr>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[40%]">Dataset</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Fonti</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Variabili</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">Data</th>
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
                                            className={`
                                                group cursor-pointer transition-colors duration-150
                                                ${isSelected ? 'bg-accent/5 border-l-2 border-accent' : 'hover:bg-slate-800/30 border-l-2 border-transparent'}
                                            `}
                                        >
                                            <td className="py-3 px-4">
                                                <div className="flex items-start gap-3">
                                                    <div className={`mt-1 p-1.5 rounded-md ${isSelected ? 'bg-accent/20 text-accent' : 'bg-slate-800 text-slate-400 group-hover:text-slate-200'}`}>
                                                        <Database size={16} />
                                                    </div>
                                                    <div>
                                                        <div className={`font-semibold text-sm ${isSelected ? 'text-accent' : 'text-slate-200 group-hover:text-white'}`}>
                                                            {dataset.name}
                                                        </div>
                                                        <div className="flex items-center gap-1.5 mt-0.5">
                                                            <code className="text-[10px] text-slate-500 font-mono bg-slate-900/50 px-1 rounded border border-slate-800">
                                                                {dataset.dataset_id.slice(0, 8)}...
                                                            </code>
                                                            <button
                                                                onClick={(e) => {
                                                                    e.stopPropagation()
                                                                    handleCopyId(dataset.dataset_id)
                                                                }}
                                                                className="opacity-0 group-hover:opacity-100 transition-opacity p-0.5 text-slate-500 hover:text-accent"
                                                                title="Copia ID"
                                                            >
                                                                <Copy size={10} />
                                                            </button>
                                                            {copiedId === dataset.dataset_id && (
                                                                <span className="text-[10px] text-emerald-400 animate-fade-in">Copied!</span>
                                                            )}
                                                        </div>
                                                    </div>
                                                </div>
                                            </td>
                                            <td className="py-3 px-4">
                                                <div className="text-sm text-slate-300">
                                                    {sourcesCount} {sourcesCount === 1 ? 'fonte' : 'fonti'}
                                                </div>
                                                <div className="text-xs text-slate-500 truncate max-w-[150px]" title={buildSourceLabel(dataset.sources_json?.[0])}>
                                                    {buildSourceLabel(dataset.sources_json?.[0])}
                                                </div>
                                            </td>
                                            <td className="py-3 px-4 text-right">
                                                <div className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-800 text-slate-300 border border-slate-700/50">
                                                    {dataset.feature_config_json?.length ?? 0} vars
                                                </div>
                                            </td>
                                            <td className="py-3 px-4 text-right text-xs text-slate-400 font-mono">
                                                {formatDate(dataset.created_utc)}
                                                <div className="text-[10px] opacity-60">UTC</div>
                                            </td>
                                        </tr>
                                    )
                                })}
                                {!filteredDatasets.length && (
                                    <tr>
                                        <td colSpan={4} className="py-12 text-center text-slate-500">
                                            {loading ? 'Caricamento in corso...' : 'Nessun dataset trovato.'}
                                        </td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>
                    {error && (
                        <div className="p-4 bg-red-900/20 border-t border-red-500/20 text-red-200 text-sm flex justify-between items-center">
                            <span>Error: {error}</span>
                            <button onClick={fetchDatasets} className="text-xs underline hover:text-white">Retry</button>
                        </div>
                    )}
                </div>

                {/* Right: Details Panel */}
                <div className="lg:col-span-1 min-h-0 flex flex-col">
                    <div className="card h-full flex flex-col p-5 bg-slate-800/40 backdrop-blur-xl border-slate-700/50 overflow-hidden sticky top-4">
                        <div className="mb-6 pb-4 border-b border-slate-700/50">
                            <p className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Dettagli selezionati</p>
                            <h3 className="text-xl font-bold text-white leading-tight">
                                {selectedDataset?.name ?? 'Nessun dataset selezionato'}
                            </h3>
                            {selectedDataset && (
                                <div className="mt-2 flex items-center gap-2">
                                    <code className="text-xs bg-black/30 text-accent px-1.5 py-0.5 rounded font-mono border border-accent/20">
                                        {selectedDataset.dataset_id}
                                    </code>
                                </div>
                            )}
                        </div>

                        {selectedDataset ? (
                            <div className="flex-1 overflow-y-auto custom-scrollbar flex flex-col gap-6 pr-2">
                                {/* Description */}
                                {selectedDataset.description && (
                                    <div>
                                        <h4 className="text-xs font-semibold text-slate-400 uppercase mb-2">Descrizione</h4>
                                        <p className="text-sm text-slate-300 leading-relaxed bg-slate-900/30 p-3 rounded-lg border border-slate-700/30">
                                            {selectedDataset.description}
                                        </p>
                                    </div>
                                )}

                                {/* Sources */}
                                <div>
                                    <h4 className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2">
                                        <Database size={12} /> Fonti Attive
                                    </h4>
                                    {selectedDataset.sources_json?.length ? (
                                        <ul className="space-y-2">
                                            {selectedDataset.sources_json.map((source, index) => {
                                                const start = formatBoundary(source.start_time)
                                                const end = formatBoundary(source.end_time)
                                                return (
                                                    <li key={index} className="text-sm bg-slate-800/50 p-3 rounded-lg border border-slate-700/50 group hover:border-accent/30 transition-colors">
                                                        <div className="font-semibold text-slate-200">{buildSourceLabel(source)}</div>
                                                        {(start || end) && (
                                                            <div className="flex items-center gap-2 mt-1.5 text-xs text-slate-500">
                                                                <span className="font-mono">{start || '∞'}</span>
                                                                <span className="text-slate-600">→</span>
                                                                <span className="font-mono">{end || '∞'}</span>
                                                            </div>
                                                        )}
                                                    </li>
                                                )
                                            })}
                                        </ul>
                                    ) : (
                                        <p className="text-sm text-slate-500 italic">Nessuna fonte registrata.</p>
                                    )}
                                </div>

                                {/* Features */}
                                <div>
                                    <h4 className="text-xs font-semibold text-slate-400 uppercase mb-3 flex items-center gap-2">
                                        <Activity size={12} /> Variabili
                                    </h4>
                                    <div className="flex flex-wrap gap-1.5">
                                        {visibleFeatures.length ? (
                                            <>
                                                {visibleFeatures.map((f, i) => (
                                                    <span key={i} className="px-2 py-1 text-xs rounded bg-slate-700/50 text-slate-300 border border-slate-600/50">
                                                        {f}
                                                    </span>
                                                ))}
                                                {moreFeatures > 0 && (
                                                    <span className="px-2 py-1 text-xs rounded bg-slate-800 text-slate-500 border border-slate-700 border-dashed">
                                                        +{moreFeatures} more
                                                    </span>
                                                )}
                                            </>
                                        ) : (
                                            <p className="text-sm text-slate-500 italic">Nessuna variabile configurata.</p>
                                        )}
                                    </div>
                                </div>

                                {/* Actions */}
                                <div className="grid grid-cols-2 gap-3 pt-4 mt-auto border-t border-slate-700/50">
                                    <button
                                        onClick={() => handleMaterialize(selectedId)}
                                        disabled={materializing}
                                        className="btn-secondary justify-center text-xs py-2 bg-indigo-500/10 text-indigo-300 border-indigo-500/30 hover:bg-indigo-500/20 hover:border-indigo-400"
                                    >
                                        <HardDrive size={14} className={materializing ? 'animate-spin' : ''} />
                                        <span>Materializza</span>
                                    </button>
                                    <button
                                        onClick={() => fetchSamples(selectedId)}
                                        disabled={samplesLoading}
                                        className="btn-secondary justify-center text-xs py-2"
                                    >
                                        <Eye size={14} className={samplesLoading ? 'animate-spin' : ''} />
                                        <span>Anteprima</span>
                                    </button>
                                </div>

                                {/* Data Preview */}
                                {showSamples && (
                                    <div className="mt-4 animate-in fade-in slide-in-from-bottom-2 duration-300">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="text-xs font-semibold text-slate-400">Anteprima (20 righe)</span>
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
                                                                    <td key={i} className="p-1.5 text-right text-slate-300">
                                                                        {typeof v === 'number' ? v.toFixed(2) : v}
                                                                    </td>
                                                                ))}
                                                            </tr>
                                                        ))}
                                                    </tbody>
                                                </table>
                                            </div>
                                        ) : (
                                            <div className="p-4 bg-slate-900/50 rounded-lg border border-slate-800 text-center">
                                                <p className="text-xs text-slate-500">Nessun dato materializzato trovato.</p>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="flex-1 flex flex-col items-center justify-center text-center opacity-40">
                                <Database size={48} className="mb-4 text-slate-600" />
                                <p className="text-sm text-slate-400 max-w-[200px]">Seleziona un dataset dalla lista per visualizzarne i dettagli completi.</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Create Modal */}
            {isCreateOpen && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 animate-in fade-in duration-200">
                    <div className="card w-full max-w-lg p-0 bg-slate-900 border-slate-700 shadow-2xl scale-100 animate-in zoom-in-95 duration-200">
                        {/* Modal Header */}
                        <div className="p-5 border-b border-slate-800 flex justify-between items-center bg-slate-800/30">
                            <div>
                                <h2 className="text-lg font-bold text-white flex items-center gap-2">
                                    <Plus size={18} className="text-accent" /> Nuovo Dataset
                                </h2>
                                <p className="text-xs text-slate-500">Configura un nuovo set di dati per il training</p>
                            </div>
                            <button onClick={() => setIsCreateOpen(false)} className="text-slate-500 hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        {/* Modal Body */}
                        <div className="p-6 space-y-5">
                            <div className="form-group">
                                <label className="text-sm font-medium text-slate-400 mb-1.5 block">Nome Dataset <span className="text-red-400">*</span></label>
                                <input
                                    type="text"
                                    value={newName}
                                    onChange={e => setNewName(e.target.value)}
                                    placeholder="es. BTC High Volatility 2024"
                                    className="input-field bg-slate-950 border-slate-700 focus:border-accent"
                                    autoFocus
                                />
                            </div>

                            <div className="form-group">
                                <label className="text-sm font-medium text-slate-400 mb-1.5 block">Descrizione</label>
                                <textarea
                                    value={newDesc}
                                    onChange={e => setNewDesc(e.target.value)}
                                    placeholder="Descrivi lo scopo di questo dataset..."
                                    className="input-field bg-slate-950 border-slate-700 focus:border-accent min-h-[80px] resize-none"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div className="form-group">
                                    <label className="text-sm font-medium text-slate-400 mb-1.5 block">Simbolo <span className="text-red-400">*</span></label>
                                    <input
                                        type="text"
                                        value={newSymbol}
                                        onChange={e => setNewSymbol(e.target.value)}
                                        placeholder="BTCUSDT"
                                        list="common-symbols"
                                        className="input-field bg-slate-950 border-slate-700 focus:border-accent"
                                    />
                                    <datalist id="common-symbols">
                                        <option value="BTCUSDT" />
                                        <option value="ETHUSDT" />
                                        <option value="SOLUSDT" />
                                        <option value="BNBUSDT" />
                                    </datalist>
                                </div>
                                <div className="form-group">
                                    <label className="text-sm font-medium text-slate-400 mb-1.5 block">Timeframe <span className="text-red-400">*</span></label>
                                    <select
                                        value={newTimeframe}
                                        onChange={e => setNewTimeframe(e.target.value)}
                                        className="input-field bg-slate-950 border-slate-700 focus:border-accent appearance-none cursor-pointer"
                                    >
                                        {['1m', '5m', '15m', '1h', '4h', '1d'].map(tf => (
                                            <option key={tf} value={tf}>{tf}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="p-3 bg-blue-500/10 border border-blue-500/20 rounded-lg text-xs text-blue-200 flex items-start gap-2">
                                <Activity size={14} className="mt-0.5 shrink-0" />
                                <div>
                                    <span className="font-semibold block mb-0.5">Feature di base incluse automaticamente</span>
                                    Verranno estratte le serie OHLCV (Open, High, Low, Close, Volume) dalla fonte dati selezionata.
                                </div>
                            </div>
                        </div>

                        {/* Modal Footer */}
                        <div className="p-5 border-t border-slate-800 flex justify-end gap-3 bg-slate-800/30 rounded-b-xl">
                            <button
                                onClick={() => setIsCreateOpen(false)}
                                className="btn-secondary text-sm py-2 px-4 hover:bg-slate-800"
                            >
                                Annulla
                            </button>
                            <button
                                onClick={submitCreate}
                                disabled={!newName || !newSymbol || creating}
                                className="btn-primary text-sm py-2 px-6 shadow-lg shadow-accent/20"
                            >
                                {creating ? <RefreshCw size={16} className="animate-spin" /> : <Plus size={16} />}
                                <span>{creating ? 'Creazione...' : 'Crea Dataset'}</span>
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </section>
    )
}

export default Datasets
