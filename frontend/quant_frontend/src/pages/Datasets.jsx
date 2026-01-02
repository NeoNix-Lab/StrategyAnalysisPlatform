import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Copy, Database, RefreshCw, Search, Plus, X, Layers, Activity, HardDrive, Eye } from 'lucide-react'
import './Datasets.css'

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
        <section className="datasets-page">
            <div className="datasets-header">
                <div>
                    <p className="datasets-label">Assets ML · Dataset</p>
                    <h1>Gestione set di dati</h1>
                    <p className="datasets-subtitle">
                        Filtra, aggiorna e ispeziona i dataset già registrati nel laboratorio quantitativo.
                    </p>
                </div>
                <div className="datasets-header-actions">
                    <button
                        type="button"
                        className="datasets-button primary"
                        onClick={handleCreateWrapper}
                        style={{ background: '#2563eb', color: 'white', border: 'none' }}
                    >
                        <Plus size={16} />
                        <span>Nuovo Dataset</span>
                    </button>
                    <button
                        type="button"
                        className="datasets-button"
                        onClick={fetchDatasets}
                        disabled={loading}
                    >
                        <RefreshCw size={14} />
                        <span>{loading ? 'Aggiornamento...' : 'Ricarica elenco'}</span>
                    </button>
                </div>
            </div>

            <div className="datasets-summary-grid">
                <div className="card summary-card">
                    <p className="summary-label">Dataset registrati</p>
                    <p className="summary-value">{datasetStats.total}</p>
                    <p className="summary-meta">{`Ultimo: ${datasetStats.newest?.name ?? '—'}`}</p>
                </div>
                <div className="card summary-card">
                    <p className="summary-label">Fonti definite</p>
                    <p className="summary-value">{datasetStats.datasetsWithSources}</p>
                    <p className="summary-meta">{`${datasetStats.totalSources} fonti totali`}</p>
                </div>
                <div className="card summary-card">
                    <p className="summary-label">Variabili</p>
                    <p className="summary-value">{datasetStats.totalFeatures}</p>
                    <p className="summary-meta">Configurazioni note</p>
                </div>
            </div>

            <div className="datasets-main">
                <div className="card datasets-table-card">
                    <div className="table-controls">
                        <label className="search-field">
                            <Search size={14} />
                            <input
                                type="search"
                                placeholder="Cerca per nome, descrizione o ID"
                                value={searchTerm}
                                onChange={(event) => setSearchTerm(event.target.value)}
                            />
                        </label>
                        <span className="table-meta">
                            {loading ? 'Caricamento...' : `${filteredDatasets.length} dataset visualizzati`}
                        </span>
                    </div>

                    <div className="dataset-table">
                        <div className="table-row header">
                            <span>Nome dataset</span>
                            <span>Fonti</span>
                            <span>Variabili</span>
                            <span>Creato il</span>
                            <span>Azioni</span>
                        </div>
                        {filteredDatasets.map((dataset) => {
                            const sourcesCount = dataset.sources_json?.length ?? 0
                            return (
                                <div
                                    key={dataset.dataset_id}
                                    className={`table-row ${selectedId === dataset.dataset_id ? 'selected' : ''}`}
                                    onClick={() => setSelectedId(dataset.dataset_id)}
                                >
                                    <div className="dataset-title">
                                        <Database size={16} />
                                        <div>
                                            <strong>{dataset.name}</strong>
                                            <small>{dataset.dataset_id}</small>
                                        </div>
                                    </div>
                                    <div className="dataset-sources">
                                        <span>
                                            {sourcesCount} {sourcesCount === 1 ? 'fonte' : 'fonti'}
                                        </span>
                                        <small>{buildSourceLabel(dataset.sources_json?.[0])}</small>
                                    </div>
                                    <div className="dataset-features">
                                        {(dataset.feature_config_json?.length ?? 0)} variabili
                                    </div>
                                    <div className="dataset-created">{formatDate(dataset.created_utc)}</div>
                                    <div className="dataset-actions">
                                        <button
                                            type="button"
                                            className="copy-btn"
                                            onClick={(event) => {
                                                event.stopPropagation()
                                                handleCopyId(dataset.dataset_id)
                                            }}
                                        >
                                            <Copy size={14} />
                                            <span>{copiedId === dataset.dataset_id ? 'ID copiato' : 'Copia ID'}</span>
                                        </button>
                                    </div>
                                </div>
                            )
                        })}
                        {!filteredDatasets.length && !loading && (
                            <div className="empty-state">
                                <p>Nessun dataset corrispondente alla ricerca.</p>
                                <button
                                    type="button"
                                    className="datasets-button small"
                                    onClick={() => setSearchTerm('')}
                                >
                                    Ripristina ricerca
                                </button>
                            </div>
                        )}
                        {!filteredDatasets.length && loading && (
                            <div className="empty-state">
                                <p>Caricamento in corso…</p>
                            </div>
                        )}
                    </div>
                    {error && (
                        <div className="datasets-error">
                            <span>{error}</span>
                            <button type="button" className="datasets-button small" onClick={fetchDatasets}>
                                Riprova
                            </button>
                        </div>
                    )}
                </div>

                <div className="card dataset-details-card">
                    <div className="details-header">
                        <div>
                            <p className="summary-label">Dettagli selezionati</p>
                            <h3>{selectedDataset?.name ?? 'Nessun dataset selezionato'}</h3>
                        </div>
                        {selectedDataset && (
                            <span className="details-id">{selectedDataset.dataset_id.slice(0, 10)}…</span>
                        )}
                    </div>
                    {selectedDataset ? (
                        <div className="details-body">
                            <p>{selectedDataset.description ?? 'Descrizione non disponibile.'}</p>
                            <div className="details-section">
                                <div className="section-title">Fonti attive</div>
                                {selectedDataset.sources_json && selectedDataset.sources_json.length ? (
                                    <ul>
                                        {selectedDataset.sources_json.map((source, index) => {
                                            const start = formatBoundary(source.start_time)
                                            const end = formatBoundary(source.end_time)
                                            return (
                                                <li key={`${source.run_id ?? 'source'}-${index}`}>
                                                    <strong>{buildSourceLabel(source)}</strong>
                                                    {(start || end) && (
                                                        <span className="source-range">
                                                            {start ? `da ${start}` : ''}
                                                            {start && end ? ' ' : ''}
                                                            {end ? `a ${end}` : ''}
                                                        </span>
                                                    )}
                                                </li>
                                            )
                                        })}
                                    </ul>
                                ) : (
                                    <p className="placeholder-text">Nessuna fonte registrata.</p>
                                )}
                            </div>

                            <div className="details-section">
                                <div className="section-title">Configurazione delle variabili</div>
                                {visibleFeatures.length ? (
                                    <div className="chips">
                                        {visibleFeatures.map((feature, idx) => (
                                            <span className="chip" key={`${feature}-${idx}`}>
                                                {feature}
                                            </span>
                                        ))}
                                        {moreFeatures > 0 && (
                                            <span className="chip more">+{moreFeatures} altre</span>
                                        )}
                                    </div>
                                ) : (
                                    <p className="placeholder-text">Configurazione delle feature mancante.</p>
                                )}
                            </div>

                            <div style={{ marginTop: '1rem', display: 'flex', gap: '0.5rem' }}>
                                <button
                                    className="datasets-button"
                                    onClick={() => handleMaterialize(selectedId)}
                                    disabled={materializing}
                                >
                                    <HardDrive size={14} />
                                    <span>{materializing ? 'Materializzazione...' : 'Materializza Dati'}</span>
                                </button>
                                <button
                                    className="datasets-button"
                                    onClick={() => fetchSamples(selectedId)}
                                    disabled={samplesLoading}
                                >
                                    <Eye size={14} />
                                    <span>{samplesLoading ? 'Caricamento...' : 'Visualizza Dati'}</span>
                                </button>
                            </div>

                            {showSamples && (
                                <div className="details-section" style={{ marginTop: '1.5rem', borderTop: '1px solid #334155', paddingTop: '1rem' }}>
                                    <div className="section-title">Anteprima Dati (Primi 20 campioni)</div>
                                    {samples.length > 0 ? (
                                        <div style={{ overflowX: 'auto', background: '#0f172a', padding: '1rem', borderRadius: '0.375rem', fontSize: '0.75rem', fontFamily: 'monospace' }}>
                                            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                                                <thead>
                                                    <tr style={{ textAlign: 'left', color: '#94a3b8' }}>
                                                        <th style={{ padding: '0.5rem' }}>Timestamp</th>
                                                        {Object.keys(samples[0].features_json).slice(0, 6).map(k => (
                                                            <th key={k} style={{ padding: '0.5rem' }}>{k}</th>
                                                        ))}
                                                    </tr>
                                                </thead>
                                                <tbody>
                                                    {samples.map((s) => (
                                                        <tr key={s.sample_id} style={{ borderBottom: '1px solid #1e293b' }}>
                                                            <td style={{ padding: '0.5rem', color: '#64748b' }}>{formatDate(s.timestamp_utc)}</td>
                                                            {Object.entries(s.features_json).slice(0, 6).map(([k, v]) => (
                                                                <td key={k} style={{ padding: '0.5rem', color: '#e2e8f0' }}>
                                                                    {typeof v === 'number' ? v.toFixed(2) : String(v)}
                                                                </td>
                                                            ))}
                                                        </tr>
                                                    ))}
                                                </tbody>
                                            </table>
                                        </div>
                                    ) : (
                                        <p className="placeholder-text">Nessun campione trovato (il dataset potrebbe non essere materializzato).</p>
                                    )}
                                </div>
                            )}

                        </div>
                    ) : (
                        <p className="placeholder-text">Seleziona un dataset dalla tabella per vedere i dettagli.</p>
                    )}
                </div>
            </div>
            {isCreateOpen && (
                <div style={{
                    position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
                    background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
                }}>
                    <div className="card" style={{ width: '500px', padding: '2rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', background: '#0f172a', border: '1px solid #334155' }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <h2 style={{ margin: 0, fontSize: '1.25rem' }}>Nuovo Dataset</h2>
                            <button onClick={() => setIsCreateOpen(false)} style={{ background: 'transparent', border: 'none', color: '#64748b', cursor: 'pointer' }}>
                                <X size={24} />
                            </button>
                        </div>

                        <div>
                            <label style={{ display: 'block', color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Nome Dataset</label>
                            <input
                                type="text"
                                value={newName}
                                onChange={e => setNewName(e.target.value)}
                                placeholder="es. BTC High Volatility"
                                style={{ width: '100%', padding: '0.75rem', background: '#1e293b', border: '1px solid #334155', borderRadius: '0.375rem', color: 'white', outline: 'none' }}
                            />
                        </div>

                        <div>
                            <label style={{ display: 'block', color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Descrizione</label>
                            <textarea
                                value={newDesc}
                                onChange={e => setNewDesc(e.target.value)}
                                placeholder="Descrizione opzionale..."
                                style={{ width: '100%', padding: '0.75rem', background: '#1e293b', border: '1px solid #334155', borderRadius: '0.375rem', color: 'white', outline: 'none', minHeight: '80px' }}
                            />
                        </div>

                        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
                            <div>
                                <label style={{ display: 'block', color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Simbolo</label>
                                <input
                                    type="text"
                                    value={newSymbol}
                                    onChange={e => setNewSymbol(e.target.value)}
                                    placeholder="BTCUSDT"
                                    style={{ width: '100%', padding: '0.75rem', background: '#1e293b', border: '1px solid #334155', borderRadius: '0.375rem', color: 'white', outline: 'none' }}
                                    list="common-symbols"
                                />
                                <datalist id="common-symbols">
                                    <option value="BTCUSDT" />
                                    <option value="ETHUSDT" />
                                    <option value="SOLUSDT" />
                                </datalist>
                            </div>
                            <div>
                                <label style={{ display: 'block', color: '#94a3b8', fontSize: '0.875rem', marginBottom: '0.5rem' }}>Timeframe</label>
                                <select
                                    value={newTimeframe}
                                    onChange={e => setNewTimeframe(e.target.value)}
                                    style={{ width: '100%', padding: '0.79rem', background: '#1e293b', border: '1px solid #334155', borderRadius: '0.375rem', color: 'white', outline: 'none' }}
                                >
                                    <option value="1m">1m</option>
                                    <option value="5m">5m</option>
                                    <option value="15m">15m</option>
                                    <option value="1h">1h</option>
                                    <option value="4h">4h</option>
                                    <option value="1d">1d</option>
                                </select>
                            </div>
                        </div>

                        <div style={{ padding: '1rem', background: 'rgba(59, 130, 246, 0.1)', border: '1px solid #1e40af', borderRadius: '0.375rem', fontSize: '0.875rem', color: '#93c5fd' }}>
                            <Activity size={14} style={{ display: 'inline', marginRight: '0.5rem' }} />
                            Verranno incluse automaticamente le feature di base: OHLCV.
                        </div>

                        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '1rem', marginTop: '1rem' }}>
                            <button
                                onClick={() => setIsCreateOpen(false)}
                                style={{ padding: '0.75rem 1.5rem', background: 'transparent', color: '#cbd5e1', border: '1px solid #334155', borderRadius: '0.375rem', cursor: 'pointer' }}
                            >
                                Annulla
                            </button>
                            <button
                                onClick={submitCreate}
                                disabled={!newName || !newSymbol || creating}
                                style={{
                                    padding: '0.75rem 1.5rem',
                                    background: (!newName || !newSymbol) ? '#334155' : '#2563eb',
                                    color: 'white', border: 'none', borderRadius: '0.375rem', cursor: 'pointer',
                                    fontWeight: 600
                                }}
                            >
                                {creating ? 'Creazione...' : 'Crea Dataset'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </section>
    )
}

export default Datasets
