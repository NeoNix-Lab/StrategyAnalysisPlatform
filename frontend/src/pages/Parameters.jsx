import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, Cell, ZAxis, Legend } from 'recharts'
import { Plus, Play, Trash2, TrendingUp } from 'lucide-react'
import axios from 'axios'

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

    useEffect(() => {
        fetchExperiments()
    }, [])

    useEffect(() => {
        if (selectedExperiment) {
            fetchRuns(selectedExperiment.experiment_id)
        }
    }, [selectedExperiment])

    const fetchExperiments = async () => {
        try {
            const res = await axios.get('http://127.0.0.1:8000/api/experiments/experiments')
            setExperiments(res.data)
        } catch (error) {
            console.error("Error fetching experiments:", error)
        }
    }

    const fetchRuns = async (experimentId) => {
        setLoading(true)
        try {
            const res = await axios.get(`http://127.0.0.1:8000/api/experiments/experiments/${experimentId}/runs`)
            setRuns(res.data)
        } catch (error) {
            console.error("Error fetching runs:", error)
        } finally {
            setLoading(false)
        }
    }

    const createExperiment = async () => {
        try {
            const res = await axios.post('http://127.0.0.1:8000/api/experiments/experiments', {
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
        const param1Values = []
        for (let v = param1Min; v <= param1Max; v += param1Step) {
            param1Values.push(v)
        }

        const param2Values = []
        for (let v = param2Min; v <= param2Max; v += param2Step) {
            param2Values.push(v)
        }

        // Simula esecuzione Grid Search
        // In produzione, qui chiameresti un endpoint che esegue il backtest per ogni combinazione
        const newRuns = []
        for (const p1 of param1Values) {
            for (const p2 of param2Values) {
                // Simula metriche random (in produzione verrebbero da backtest reale)
                const winRate = 40 + Math.random() * 30
                const profitFactor = 0.8 + Math.random() * 1.5
                const sharpe = -0.5 + Math.random() * 2

                const run = {
                    experiment_id: selectedExperiment.experiment_id,
                    parameters: {
                        [param1Name]: p1,
                        [param2Name]: p2
                    },
                    metrics: {
                        win_rate: winRate,
                        profit_factor: profitFactor,
                        sharpe_ratio: sharpe,
                        net_profit: (profitFactor - 1) * 1000 + Math.random() * 500
                    }
                }

                try {
                    const res = await axios.post('http://127.0.0.1:8000/api/experiments/experiments/runs', run)
                    newRuns.push(res.data)
                } catch (error) {
                    console.error("Error creating run:", error)
                }
            }
        }

        setRuns([...runs, ...newRuns])
        setLoading(false)
    }

    // Prepare heatmap data
    const heatmapData = runs.map(run => ({
        x: run.parameters[param1Name],
        y: run.parameters[param2Name],
        z: run.metrics.sharpe_ratio || 0,
        pf: run.metrics.profit_factor || 0
    }))

    // Best run
    const bestRun = runs.length > 0
        ? runs.reduce((best, current) =>
            (current.metrics.sharpe_ratio || 0) > (best.metrics.sharpe_ratio || 0) ? current : best
        )
        : null

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
                        <h3>Grid Search Configuration</h3>
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
                                <h3>Best Configuration</h3>
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
                                <div className="best-param">
                                    <span className="label">Sharpe Ratio:</span>
                                    <span className="value text-success">{bestRun.metrics.sharpe_ratio?.toFixed(2)}</span>
                                </div>
                                <div className="best-param">
                                    <span className="label">Profit Factor:</span>
                                    <span className="value">{bestRun.metrics.profit_factor?.toFixed(2)}</span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="card chart-card" style={{ height: '500px' }}>
                        <h3>Parameter Heatmap (Sharpe Ratio)</h3>
                        <div className="chart-container">
                            <ResponsiveContainer width="100%" height="100%">
                                <ScatterChart>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis type="number" dataKey="x" name={param1Name} stroke="#94a3b8" />
                                    <YAxis type="number" dataKey="y" name={param2Name} stroke="#94a3b8" />
                                    <ZAxis type="number" dataKey="z" range={[100, 1000]} name="Sharpe" />
                                    <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                    <Legend />
                                    <Scatter name="Runs" data={heatmapData} fill="#38bdf8">
                                        {heatmapData.map((entry, index) => (
                                            <Cell key={`cell-${index}`} fill={entry.z > 0.5 ? '#4ade80' : entry.z > 0 ? '#fbbf24' : '#f87171'} />
                                        ))}
                                    </Scatter>
                                </ScatterChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default Parameters
