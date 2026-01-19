import { useEffect, useMemo, useState } from 'react'
import { CartesianGrid, Cell, Legend, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis, ZAxis, LineChart, Line, AreaChart, Area } from 'recharts'
import { Plus, Play, Pause, TrendingUp } from 'lucide-react'
import api from '../api/axios'

const METRIC_LABELS = {
    sharpe_ratio: 'Sharpe Ratio',
    profit_factor: 'Profit Factor',
    net_profit: 'Net Profit',
    win_rate: 'Win Rate'
}

const deriveParamSpace = (runs) => {
    const space = {}
    runs.forEach(run => {
        Object.entries(run.parameters || {}).forEach(([key, value]) => {
            if (!space[key]) space[key] = new Set()
            space[key].add(value)
        })
    })

    const result = {}
    Object.entries(space).forEach(([key, values]) => {
        const arr = Array.from(values)
        const allNumeric = arr.every(v => !isNaN(parseFloat(v)))
        result[key] = arr.sort((a, b) => allNumeric ? parseFloat(a) - parseFloat(b) : String(a).localeCompare(String(b)))
    })
    return result
}

const computeSensitivity = (runs, space) => {
    const paramSpace = space || deriveParamSpace(runs)
    return Object.entries(paramSpace).map(([param, values]) => {
        const series = values.map(value => {
            const matching = runs.filter(r => (r.parameters || {})[param] === value)
            const metrics = ['sharpe_ratio', 'profit_factor', 'net_profit', 'win_rate'].reduce((acc, key) => {
                const vals = matching.map(r => (r.metrics || {})[key] || 0)
                const avg = vals.length ? vals.reduce((a, b) => a + b, 0) / vals.length : 0
                acc[key] = Number(avg.toFixed(4))
                return acc
            }, {})
            return { value, ...metrics }
        })
        return { parameter: param, series }
    })
}

const buildHeatmapData = (runs, paramX, paramY) => {
    const grid = {}
    runs.forEach(run => {
        const params = run.parameters || {}
        const metrics = run.metrics || {}
        const x = params[paramX]
        const y = params[paramY]
        if (x === undefined || y === undefined) return

        const key = `${x}-${y}`
        if (!grid[key]) {
            grid[key] = {
                x,
                y,
                count: 0,
                sharpe_ratio: 0,
                profit_factor: 0,
                net_profit: 0,
                win_rate: 0
            }
        }

        grid[key].count += 1
        grid[key].sharpe_ratio += metrics.sharpe_ratio ?? 0
        grid[key].profit_factor += metrics.profit_factor ?? 0
        grid[key].net_profit += metrics.net_profit ?? 0
        grid[key].win_rate += metrics.win_rate ?? 0
    })

    return Object.values(grid).map(cell => ({
        ...cell,
        sharpe_ratio: cell.sharpe_ratio / cell.count,
        profit_factor: cell.profit_factor / cell.count,
        net_profit: cell.net_profit / cell.count,
        win_rate: cell.win_rate / cell.count
    }))
}

const clamp = (value, min, max) => Math.max(min, Math.min(max, value))

const colorForMetric = (value, min, max) => {
    if (value === undefined || value === null) return '#1f2937'
    const range = max - min || 1
    const t = clamp((value - min) / range, 0, 1)
    const lerp = (a, b, p) => Math.round(a + (b - a) * p)
    // Red -> Yellow -> Green
    const mid = 0.5
    if (t <= mid) {
        const p = t / mid
        const r = lerp(248, 251, p)
        const g = lerp(113, 191, p)
        const b = lerp(113, 36, p)
        return `rgb(${r}, ${g}, ${b})`
    }
    const p = (t - mid) / (1 - mid)
    const r = lerp(251, 74, p)
    const g = lerp(191, 222, p)
    const b = lerp(36, 128, p)
    return `rgb(${r}, ${g}, ${b})`
}

const Parameters = () => {
    const [experiments, setExperiments] = useState([])
    const [selectedExperiment, setSelectedExperiment] = useState(null)
    const [runs, setRuns] = useState([])
    const [loading, setLoading] = useState(false)

    // New Experiment Form
    const [showNewExperiment, setShowNewExperiment] = useState(false)
    const [newExpName, setNewExpName] = useState('')
    const [newExpDesc, setNewExpDesc] = useState('')

    // Grid Search Parameters
    const [param1Name, setParam1Name] = useState('stop_loss')
    const [param1Min, setParam1Min] = useState(10)
    const [param1Max, setParam1Max] = useState(50)
    const [param1Step, setParam1Step] = useState(10)

    const [param2Name, setParam2Name] = useState('take_profit')
    const [param2Min, setParam2Min] = useState(20)
    const [param2Max, setParam2Max] = useState(100)
    const [param2Step, setParam2Step] = useState(20)

    const [param3Enabled, setParam3Enabled] = useState(true)
    const [param3Name, setParam3Name] = useState('lookback')
    const [param3Min, setParam3Min] = useState(5)
    const [param3Max, setParam3Max] = useState(30)
    const [param3Step, setParam3Step] = useState(5)

    const [selectedMetric, setSelectedMetric] = useState('sharpe_ratio')
    const [paramSpace, setParamSpace] = useState({})
    const [sensitivity, setSensitivity] = useState([])
    const [currentSliceIndex, setCurrentSliceIndex] = useState(0)
    const [isPlaying, setIsPlaying] = useState(false)

    useEffect(() => {
        fetchExperiments()
    }, [])

    useEffect(() => {
        if (selectedExperiment) {
            fetchRuns(selectedExperiment.experiment_id)
        }
    }, [selectedExperiment])

    useEffect(() => {
        setCurrentSliceIndex(0)
    }, [param3Name, paramSpace])

    useEffect(() => {
        if (!isPlaying) return
        const slices = paramSpace[param3Name] || []
        if (slices.length <= 1) {
            setIsPlaying(false)
            return
        }
        const interval = setInterval(() => {
            setCurrentSliceIndex((prev) => (prev + 1) % slices.length)
        }, 1200)
        return () => clearInterval(interval)
    }, [isPlaying, paramSpace, param3Name])

    const fetchExperiments = async () => {
        try {
            const res = await api.get('/experiments/experiments')
            setExperiments(res.data)
        } catch (error) {
            console.error("Error fetching experiments:", error)
        }
    }

    const syncDerivedData = (runsPayload, spacePayload, sensitivityPayload) => {
        const derivedSpace = spacePayload || deriveParamSpace(runsPayload)
        const derivedSensitivity = sensitivityPayload || computeSensitivity(runsPayload, derivedSpace)
        setParamSpace(derivedSpace)
        setSensitivity(derivedSensitivity)
    }

    const fetchRuns = async (experimentId) => {
        setLoading(true)
        try {
            const res = await api.get(`/experiments/experiments/${experimentId}/runs`)
            setRuns(res.data)
            syncDerivedData(res.data)
        } catch (error) {
            console.error("Error fetching runs:", error)
        } finally {
            setLoading(false)
        }
    }

    const createExperiment = async () => {
        try {
            const res = await api.post('/experiments/experiments', {
                name: newExpName,
                description: newExpDesc,
                base_config: {}
            })
            setExperiments([...experiments, res.data])
            setShowNewExperiment(false)
            setNewExpName('')
            setNewExpDesc('')
        } catch (error) {
            console.error("Error creating experiment:", error)
        }
    }

    const runGridSearch = async () => {
        if (!selectedExperiment) return

        setLoading(true)
        try {
            const parameters = [
                { name: param1Name, min: Number(param1Min), max: Number(param1Max), step: Number(param1Step) },
                { name: param2Name, min: Number(param2Min), max: Number(param2Max), step: Number(param2Step) }
            ]
            if (param3Enabled) {
                parameters.push({ name: param3Name, min: Number(param3Min), max: Number(param3Max), step: Number(param3Step) })
            }

            const res = await api.post(`/experiments/experiments/${selectedExperiment.experiment_id}/grid-search`, {
                parameters,
                metric: selectedMetric
            })
            setRuns(res.data.runs || [])
            syncDerivedData(res.data.runs || [], res.data.param_space, res.data.sensitivity)
        } catch (error) {
            console.error("Error running grid search:", error)
        } finally {
            setLoading(false)
        }
    }

    const sliceValues = paramSpace[param3Name] || []
    const currentSliceValue = sliceValues[currentSliceIndex] ?? sliceValues[0]
    const tensorActive = param3Enabled && sliceValues.length > 0

    const filteredRuns = useMemo(() => {
        if (!tensorActive || currentSliceValue === undefined) return runs
        return runs.filter(r => (r.parameters || {})[param3Name] === currentSliceValue)
    }, [runs, tensorActive, currentSliceValue, param3Name])

    const heatmapData = useMemo(() => buildHeatmapData(filteredRuns, param1Name, param2Name), [filteredRuns, param1Name, param2Name])
    const metricRange = useMemo(() => {
        if (!heatmapData.length) return { min: 0, max: 1 }
        const values = heatmapData.map(h => h[selectedMetric] ?? 0)
        return { min: Math.min(...values), max: Math.max(...values) }
    }, [heatmapData, selectedMetric])

    const bestRun = useMemo(() => {
        if (!runs.length) return null
        return runs.reduce((best, current) => {
            const currentMetric = (current.metrics || {})[selectedMetric] ?? -Infinity
            const bestMetric = (best.metrics || {})[selectedMetric] ?? -Infinity
            return currentMetric > bestMetric ? current : best
        }, runs[0])
    }, [runs, selectedMetric])

    const topSliceRuns = useMemo(() => {
        const target = tensorActive ? filteredRuns : runs
        return [...target].sort((a, b) => ((b.metrics || {})[selectedMetric] ?? 0) - ((a.metrics || {})[selectedMetric] ?? 0)).slice(0, 3)
    }, [filteredRuns, runs, tensorActive, selectedMetric])

    return (
        <div className="parameters-container">
            <div className="parameters-header">
                <h2>Parameter Lab</h2>
                <button className="btn-primary" onClick={() => setShowNewExperiment(true)}>
                    <Plus size={16} /> New Experiment
                </button>
            </div>

            {showNewExperiment && (
                <div className="card" style={{ marginBottom: '1.5rem' }}>
                    <h3>Create New Experiment</h3>
                    <div className="form-group">
                        <label>Name</label>
                        <input
                            type="text"
                            value={newExpName}
                            onChange={(e) => setNewExpName(e.target.value)}
                            placeholder="e.g., Stop Loss Optimization"
                            className="input-field"
                        />
                    </div>
                    <div className="form-group">
                        <label>Description</label>
                        <textarea
                            value={newExpDesc}
                            onChange={(e) => setNewExpDesc(e.target.value)}
                            placeholder="Optional description..."
                            className="input-field"
                            rows={3}
                        />
                    </div>
                    <div className="form-actions">
                        <button className="btn-secondary" onClick={() => setShowNewExperiment(false)}>Cancel</button>
                        <button className="btn-primary" onClick={createExperiment}>Create</button>
                    </div>
                </div>
            )}

            <div className="experiments-grid">
                <div className="card experiments-list">
                    <h3>Experiments</h3>
                    {experiments.length === 0 ? (
                        <p className="text-secondary">No experiments yet. Create one to get started.</p>
                    ) : (
                        <div className="experiment-items">
                            {experiments.map(exp => (
                                <div
                                    key={exp.experiment_id}
                                    className={`experiment-item ${selectedExperiment?.experiment_id === exp.experiment_id ? 'active' : ''}`}
                                    onClick={() => setSelectedExperiment(exp)}
                                >
                                    <div className="experiment-name">{exp.name}</div>
                                    <div className="experiment-meta">{new Date(exp.created_at).toLocaleDateString()}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                {selectedExperiment && (
                    <div className="card grid-search-panel">
                        <div className="grid-search-header">
                            <h3>Grid Search Configuration</h3>
                            <div className="metric-selector">
                                <label>Metric</label>
                                <select value={selectedMetric} onChange={(e) => setSelectedMetric(e.target.value)} className="input-field-sm">
                                    {Object.entries(METRIC_LABELS).map(([key, label]) => (
                                        <option key={key} value={key}>{label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                        <div className="param-config">
                            <div className="param-row">
                                <label>Parameter 1</label>
                                <input type="text" value={param1Name} onChange={(e) => setParam1Name(e.target.value)} className="input-field-sm" />
                                <input type="number" value={param1Min} onChange={(e) => setParam1Min(Number(e.target.value))} className="input-field-sm" placeholder="Min" />
                                <input type="number" value={param1Max} onChange={(e) => setParam1Max(Number(e.target.value))} className="input-field-sm" placeholder="Max" />
                                <input type="number" value={param1Step} onChange={(e) => setParam1Step(Number(e.target.value))} className="input-field-sm" placeholder="Step" />
                            </div>
                            <div className="param-row">
                                <label>Parameter 2</label>
                                <input type="text" value={param2Name} onChange={(e) => setParam2Name(e.target.value)} className="input-field-sm" />
                                <input type="number" value={param2Min} onChange={(e) => setParam2Min(Number(e.target.value))} className="input-field-sm" placeholder="Min" />
                                <input type="number" value={param2Max} onChange={(e) => setParam2Max(Number(e.target.value))} className="input-field-sm" placeholder="Max" />
                                <input type="number" value={param2Step} onChange={(e) => setParam2Step(Number(e.target.value))} className="input-field-sm" placeholder="Step" />
                            </div>
                            <div className="param-row">
                                <label>Tensor Slice (Param 3)</label>
                                <input type="text" value={param3Name} onChange={(e) => setParam3Name(e.target.value)} className="input-field-sm" disabled={!param3Enabled} />
                                <input type="number" value={param3Min} onChange={(e) => setParam3Min(Number(e.target.value))} className="input-field-sm" placeholder="Min" disabled={!param3Enabled} />
                                <input type="number" value={param3Max} onChange={(e) => setParam3Max(Number(e.target.value))} className="input-field-sm" placeholder="Max" disabled={!param3Enabled} />
                                <input type="number" value={param3Step} onChange={(e) => setParam3Step(Number(e.target.value))} className="input-field-sm" placeholder="Step" disabled={!param3Enabled} />
                                <label className="toggle">
                                    <input type="checkbox" checked={param3Enabled} onChange={(e) => setParam3Enabled(e.target.checked)} />
                                    <span>Enable Tensor Viz</span>
                                </label>
                            </div>
                        </div>
                        <button className="btn-primary" onClick={runGridSearch} disabled={loading}>
                            <Play size={16} /> {loading ? 'Running...' : 'Run Grid Search'}
                        </button>
                    </div>
                )}
            </div>

            {selectedExperiment && runs.length > 0 && (
                <>
                    {bestRun && (
                        <div className="card best-run-card">
                            <div className="best-run-header">
                                <TrendingUp size={20} color="#4ade80" />
                                <h3>Best Configuration ({METRIC_LABELS[selectedMetric]})</h3>
                            </div>
                            <div className="best-run-content">
                                <div className="best-param">
                                    <span className="label">{param1Name}:</span>
                                    <span className="value">{bestRun.parameters[param1Name]}</span>
                                </div>
                                <div className="best-param">
                                    <span className="label">{param2Name}:</span>
                                    <span className="value">{bestRun.parameters[param2Name]}</span>
                                </div>
                                {param3Enabled && bestRun.parameters[param3Name] !== undefined && (
                                    <div className="best-param">
                                        <span className="label">{param3Name}:</span>
                                        <span className="value">{bestRun.parameters[param3Name]}</span>
                                    </div>
                                )}
                                <div className="best-param">
                                    <span className="label">{METRIC_LABELS[selectedMetric]}:</span>
                                    <span className="value text-success">{(bestRun.metrics[selectedMetric] ?? 0).toFixed(2)}</span>
                                </div>
                                <div className="best-param">
                                    <span className="label">Profit Factor:</span>
                                    <span className="value">{bestRun.metrics.profit_factor?.toFixed(2)}</span>
                                </div>
                                <div className="best-param">
                                    <span className="label">Net Profit:</span>
                                    <span className="value">{bestRun.metrics.net_profit?.toFixed(0)} USD</span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="charts-grid">
                        <div className="card chart-card" style={{ height: '520px' }}>
                            <div className="heatmap-header">
                                <div>
                                    <h3>Heatmap {METRIC_LABELS[selectedMetric]}</h3>
                                    {tensorActive && (
                                        <p className="text-secondary">Slice: {param3Name} = {currentSliceValue}</p>
                                    )}
                                </div>
                                <div className="heatmap-legend">
                                    <span className="legend-badge">Tensor Visualization</span>
                                    <div className="legend-scale">
                                        <span>Low</span>
                                        <div className="legend-gradient"></div>
                                        <span>High</span>
                                    </div>
                                </div>
                            </div>
                            <div className="chart-container">
                                <ResponsiveContainer width="100%" height="100%">
                                    <ScatterChart>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis type="number" dataKey="x" name={param1Name} stroke="#94a3b8" />
                                        <YAxis type="number" dataKey="y" name={param2Name} stroke="#94a3b8" />
                                        <ZAxis type="number" dataKey={selectedMetric} range={[100, 900]} name={METRIC_LABELS[selectedMetric]} />
                                        <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                        <Legend />
                                        <Scatter name="Runs" data={heatmapData} fill="#38bdf8">
                                            {heatmapData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={colorForMetric(entry[selectedMetric], metricRange.min, metricRange.max)} />
                                            ))}
                                        </Scatter>
                                    </ScatterChart>
                                </ResponsiveContainer>
                            </div>
                        </div>

                        <div className="card tensor-card">
                            <div className="heatmap-header">
                                <div>
                                    <h3>Tensor Visualization</h3>
                                    <p className="text-secondary">Animate the heatmap across {param3Name || 'param3'}</p>
                                </div>
                                <button className="btn-secondary" onClick={() => setIsPlaying(!isPlaying)} disabled={!tensorActive}>
                                    {isPlaying ? <Pause size={16} /> : <Play size={16} />} {isPlaying ? 'Stop' : 'Play'}
                                </button>
                            </div>
                            <div className="tensor-slider">
                                <input
                                    type="range"
                                    min={0}
                                    max={Math.max((sliceValues.length || 1) - 1, 0)}
                                    value={currentSliceIndex}
                                    onChange={(e) => setCurrentSliceIndex(Number(e.target.value))}
                                    disabled={!tensorActive}
                                />
                                <div className="tensor-meta">
                                    <span className="slice-label">Slice value</span>
                                    <span className="slice-value">{tensorActive ? currentSliceValue : 'N/A'}</span>
                                </div>
                            </div>
                            <div className="tensor-top">
                                <h4>Top configs in slice</h4>
                                {topSliceRuns.length === 0 ? (
                                    <p className="text-secondary">Run a grid search to populate tensor slices.</p>
                                ) : (
                                    topSliceRuns.map((run, idx) => (
                                        <div key={run.run_id} className="tensor-row">
                                            <span className="rank">#{idx + 1}</span>
                                            <div className="tensor-row-params">
                                                <span>{param1Name}: {run.parameters[param1Name]}</span>
                                                <span>{param2Name}: {run.parameters[param2Name]}</span>
                                                {param3Enabled && run.parameters[param3Name] !== undefined && (
                                                    <span>{param3Name}: {run.parameters[param3Name]}</span>
                                                )}
                                            </div>
                                            <div className="tensor-row-metrics">
                                                <span>{METRIC_LABELS[selectedMetric]}: {(run.metrics[selectedMetric] ?? 0).toFixed(2)}</span>
                                                <span>PF: {(run.metrics.profit_factor ?? 0).toFixed(2)}</span>
                                            </div>
                                        </div>
                                    ))
                                )}
                            </div>
                        </div>
                    </div>

                    <div className="card sensitivity-card">
                        <div className="heatmap-header">
                            <h3>Sensitivity Analysis</h3>
                            <p className="text-secondary">Average impact of each parameter on {METRIC_LABELS[selectedMetric]} and Net Profit</p>
                        </div>
                        <div className="sensitivity-grid">
                            {sensitivity.map((item) => (
                                <div key={item.parameter} className="sensitivity-item">
                                    <div className="sensitivity-title">{item.parameter}</div>
                                    <ResponsiveContainer width="100%" height={150}>
                                        <LineChart data={item.series}>
                                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                            <XAxis dataKey="value" stroke="#94a3b8" />
                                            <YAxis stroke="#94a3b8" />
                                            <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                            <Line type="monotone" dataKey={selectedMetric} stroke="#38bdf8" strokeWidth={2} dot={false} name={METRIC_LABELS[selectedMetric]} />
                                        </LineChart>
                                    </ResponsiveContainer>
                                    <ResponsiveContainer width="100%" height={80}>
                                        <AreaChart data={item.series}>
                                            <Area type="monotone" dataKey="net_profit" stroke="#4ade80" fill="rgba(74, 222, 128, 0.15)" name="Net Profit" />
                                        </AreaChart>
                                    </ResponsiveContainer>
                                </div>
                            ))}
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default Parameters
