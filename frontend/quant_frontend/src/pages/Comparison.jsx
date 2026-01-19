import React, { useState, useEffect, useMemo } from 'react'
import { useStrategy } from '../context/StrategyContext'
import api from '../api/axios'
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend
} from 'recharts'
import {
    Activity, ArrowRight, TrendingUp, DollarSign, AlertTriangle,
    X, Plus, BarChart2, Sigma, Layers, ChevronRight, ChevronDown
} from 'lucide-react'

// Enhanced Selector Component for Cross-Strategy/Cross-Instance Selection
const ComparisonSelector = ({ mode, onSelect }) => {
    const { strategies: contextStrategies } = useStrategy()
    const [strategies, setStrategies] = useState(contextStrategies || [])

    // Selection State
    const [selectedStrategyId, setSelectedStrategyId] = useState(null)
    const [selectedInstanceId, setSelectedInstanceId] = useState(null)

    // Data State
    const [instances, setInstances] = useState([])
    const [runs, setRuns] = useState([])
    const [error, setError] = useState(null)

    // Sync strategies if context ones update (or fetch if missing)
    useEffect(() => {
        if (!contextStrategies || contextStrategies.length === 0) {
            api.get('/strategies/')
                .then(res => setStrategies(res.data))
                .catch(err => console.error("Failed to fetch selector strategies", err))
        } else {
            setStrategies(contextStrategies)
        }
    }, [contextStrategies])

    // Auto-select first strategy
    useEffect(() => {
        if (strategies.length > 0 && !selectedStrategyId) {
            setSelectedStrategyId(strategies[0].strategy_id)
        }
    }, [strategies])

    // Fetch Instances when Strategy Changes
    useEffect(() => {
        if (!selectedStrategyId) return
        setInstances([])
        setRuns([])
        setSelectedInstanceId(null)

        api.get(`/strategies/${selectedStrategyId}/instances`)
            .then(res => {
                setInstances(res.data)
                if (res.data.length > 0 && mode === 'runs') {
                    // Pre-select first instance to show runs immediately
                    setSelectedInstanceId(res.data[0].instance_id)
                }
            })
            .catch(err => console.error("Selector: Failed to fetch instances", err))

    }, [selectedStrategyId, mode])

    // Fetch Runs when Instance Changes (Only in Runs Mode)
    useEffect(() => {
        if (mode !== 'runs' || !selectedInstanceId) return
        setRuns([])

        api.get(`/runs/instance/${selectedInstanceId}`)
            .then(res => {
                // Sort descending by date
                setRuns(res.data.sort((a, b) => new Date(b.created_at) - new Date(a.created_at)))
            })
            .catch(err => console.error("Selector: Failed to fetch runs", err))
    }, [selectedInstanceId, mode])

    const handleItemClick = (id) => {
        onSelect(id)
    }

    return (
        <div className="flex flex-col gap-3 min-w-[300px] max-w-[350px]">
            {/* 1. Strategy Selector */}
            <div className="flex flex-col gap-1">
                <span className="text-[10px] uppercase font-bold text-text-muted">Source Strategy</span>
                <select
                    value={selectedStrategyId || ''}
                    onChange={(e) => setSelectedStrategyId(e.target.value)}
                    className="bg-bg-secondary border border-slate-700 rounded-lg p-2 text-sm text-text-primary focus:border-accent focus:outline-none"
                >
                    {strategies.map(s => (
                        <option key={s.strategy_id} value={s.strategy_id}>{s.name || s.strategy_id}</option>
                    ))}
                </select>
            </div>

            {/* 2. Instance Selector (In Runs Mode) */}
            {mode === 'runs' && (
                <div className="flex flex-col gap-1">
                    <span className="text-[10px] uppercase font-bold text-text-muted">Source Instance</span>
                    <select
                        value={selectedInstanceId || ''}
                        onChange={(e) => setSelectedInstanceId(e.target.value)}
                        className="bg-bg-secondary border border-slate-700 rounded-lg p-2 text-sm text-text-primary focus:border-accent focus:outline-none"
                        disabled={instances.length === 0}
                    >
                        {instances.length === 0 && <option>No Instances</option>}
                        {instances.map(i => (
                            <option key={i.instance_id} value={i.instance_id}>
                                {i.instance_id.substring(0, 8)}... ({Object.keys(i.parameters_json || {}).length} params)
                            </option>
                        ))}
                    </select>
                </div>
            )}

            {/* 3. List of Selectable Items */}
            <div className="flex flex-col gap-1 mt-2">
                <span className="text-[10px] uppercase font-bold text-accent mb-1">
                    Select {mode === 'runs' ? 'Run' : 'Instance'} to Add
                </span>
                <div className="bg-bg-secondary/50 border border-slate-700 rounded-lg max-h-[250px] overflow-y-auto custom-scrollbar">
                    {mode === 'instances' ? (
                        // INSTANCE LIST
                        instances.length > 0 ? (
                            instances.map(inst => (
                                <div
                                    key={inst.instance_id}
                                    onClick={() => handleItemClick(inst.instance_id)}
                                    className="p-3 border-b border-white/5 last:border-0 hover:bg-accent/20 cursor-pointer transition-colors group"
                                >
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="font-mono text-xs font-bold text-text-primary group-hover:text-accent">
                                            {inst.instance_id.substring(0, 8)}
                                        </span>
                                        <ChevronRight size={14} className="text-slate-600 group-hover:text-accent opacity-0 group-hover:opacity-100 transition-all" />
                                    </div>
                                    <div className="text-[10px] text-text-secondary truncate">
                                        {inst.parameters_json ? JSON.stringify(inst.parameters_json) : 'No Params'}
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="p-4 text-center text-xs text-text-muted">No instances found for this strategy.</div>
                        )
                    ) : (
                        // RUN LIST
                        runs.length > 0 ? (
                            runs.map(run => (
                                <div
                                    key={run.run_id}
                                    onClick={() => handleItemClick(run.run_id)}
                                    className="p-3 border-b border-white/5 last:border-0 hover:bg-accent/20 cursor-pointer transition-colors group"
                                >
                                    <div className="flex justify-between items-center mb-1">
                                        <span className="font-mono text-xs font-bold text-text-primary group-hover:text-accent">
                                            {run.run_id.substring(0, 8)}...
                                        </span>
                                        <span className="text-[10px] text-text-muted">
                                            {new Date(run.created_at).toLocaleDateString()}
                                        </span>
                                    </div>
                                    <div className="flex gap-2">
                                        {run.metrics_json && (
                                            <>
                                                <span className={`text-[10px] font-bold ${run.metrics_json.net_profit >= 0 ? 'text-green-400' : 'text-red-400'}`}>
                                                    {run.metrics_json.net_profit.toFixed(1)}€
                                                </span>
                                                <span className="text-[10px] text-text-secondary">
                                                    Win: {run.metrics_json.win_rate}%
                                                </span>
                                            </>
                                        )}
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="p-4 text-center text-xs text-text-muted">
                                {selectedInstanceId ? "No runs found for this instance." : "Select an instance above."}
                            </div>
                        )
                    )}
                </div>
            </div>
        </div>
    )
}

const Comparison = () => {
    const { runs: contextRuns, instances: contextInstances } = useStrategy()
    const [comparisonMode, setComparisonMode] = useState('runs') // 'runs' | 'instances'

    // State for Runs Mode
    const [selectedRunIds, setSelectedRunIds] = useState([])
    const [runComparisonData, setRunComparisonData] = useState({})

    // State for Instances Mode
    const [selectedInstanceIds, setSelectedInstanceIds] = useState([])
    const [instanceComparisonData, setInstanceComparisonData] = useState({})

    const [loading, setLoading] = useState(false)
    const [availableColors] = useState([
        '#8b5cf6', // Violet
        '#4ade80', // Green
        '#f472b6', // Pink
        '#38bdf8', // Sky
        '#facc15', // Yellow
        '#f87171'  // Red
    ])

    // --- FETCH RUN DATA ---
    useEffect(() => {
        if (comparisonMode !== 'runs') return
        const fetchMissingRuns = async () => {
            const missingIds = selectedRunIds.filter(id => !runComparisonData[id])
            if (missingIds.length === 0) return

            setLoading(true)
            const newData = { ...runComparisonData }

            try {
                await Promise.all(missingIds.map(async (runId) => {
                    try {
                        const [runRes, tradesRes] = await Promise.all([
                            api.get(`/runs/${runId}`),
                            api.get(`/runs/${runId}/trades`)
                        ])

                        const run = runRes.data
                        const trades = tradesRes.data || []
                        const stats = run.metrics_json || createEmptyStats()
                        const equityCurve = processEquityCurve(run, trades)

                        newData[runId] = { run, stats, trades, equityCurve }
                    } catch (err) {
                        console.error(`Failed to fetch run ${runId}`, err)
                    }
                }))
                setRunComparisonData(newData)
            } finally {
                setLoading(false)
            }
        }
        fetchMissingRuns()
    }, [selectedRunIds, runComparisonData, comparisonMode])


    // --- FETCH INSTANCE DATA (Aggregated from ALL runs) ---
    useEffect(() => {
        if (comparisonMode !== 'instances') return
        const fetchMissingInstances = async () => {
            const missingIds = selectedInstanceIds.filter(id => !instanceComparisonData[id])
            if (missingIds.length === 0) return

            setLoading(true)
            const newData = { ...instanceComparisonData }

            try {
                await Promise.all(missingIds.map(async (instanceId) => {
                    try {
                        // 1. Get all runs for the instance
                        const runsRes = await api.get(`/runs/instance/${instanceId}`)
                        const instanceRuns = runsRes.data || []

                        if (instanceRuns.length === 0) {
                            newData[instanceId] = { stats: createEmptyStats(), equityCurve: [], runCount: 0, instanceId }
                            return
                        }

                        // 2. Aggregate Stats
                        const aggregatedStats = createEmptyStats()
                        let totalEquityCurves = []

                        await Promise.all(instanceRuns.map(async (run) => {
                            let metrics = run.metrics_json
                            if (!metrics) {
                                try {
                                    const fullRunRes = await api.get(`/runs/${run.run_id}`)
                                    metrics = fullRunRes.data.metrics_json
                                } catch (e) { console.warn("Failed to fetch full run", run.run_id) }
                            }

                            if (metrics) {
                                Object.keys(aggregatedStats).forEach(key => {
                                    if (aggregatedStats[key] !== undefined) {
                                        aggregatedStats[key] += (metrics[key] || 0)
                                    }
                                })
                            }

                            // Try to fetch trades for curve construction
                            try {
                                const tradesRes = await api.get(`/runs/${run.run_id}/trades`)
                                const trades = tradesRes.data || []
                                const curve = processEquityCurve(run, trades)
                                if (curve.length > 0) totalEquityCurves.push(curve)
                            } catch (e) { }

                        }))

                        // Average the stats
                        const count = instanceRuns.length
                        Object.keys(aggregatedStats).forEach(key => {
                            aggregatedStats[key] = aggregatedStats[key] / count
                        })

                        // Average the Equity Curve
                        let maxLen = 0
                        totalEquityCurves.forEach(c => maxLen = Math.max(maxLen, c.length))

                        const avgEquityCurve = []
                        for (let i = 0; i < maxLen; i++) {
                            let sum = 0
                            let validCount = 0
                            totalEquityCurves.forEach(c => {
                                let val = null
                                if (c[i]) val = c[i].pnl
                                else if (c.length > 0) val = c[c.length - 1].pnl

                                if (val !== null) {
                                    sum += val
                                    validCount++
                                }
                            })
                            if (validCount > 0) {
                                avgEquityCurve.push({
                                    index: i,
                                    pnl: sum / validCount,
                                    time: i
                                })
                            }
                        }

                        newData[instanceId] = {
                            stats: aggregatedStats,
                            equityCurve: avgEquityCurve,
                            runCount: count,
                            instanceId
                        }

                    } catch (err) {
                        console.error(`Failed to fetch instance ${instanceId}`, err)
                    }
                }))
                setInstanceComparisonData(newData)
            } finally {
                setLoading(false)
            }
        }
        fetchMissingInstances()
    }, [selectedInstanceIds, instanceComparisonData, comparisonMode])

    // --- HELPERS ---
    const createEmptyStats = () => ({
        net_profit: 0, win_rate: 0, profit_factor: 0, total_trades: 0,
        max_drawdown: 0, sharpe_ratio: 0, sortino_ratio: 0
    })

    const processEquityCurve = (run, trades) => {
        if (run.metrics_json?.equity_curve && run.metrics_json.equity_curve.length > 0) {
            return run.metrics_json.equity_curve.map((p, i) => ({
                index: i, pnl: p.pnl, time: p.time
            }))
        }
        // Reconstruct
        let runningPnL = 0
        const sortedTrades = [...trades].sort((a, b) => new Date(a.exit_time) - new Date(b.exit_time))
        return sortedTrades.map((t, i) => {
            runningPnL += (t.pnl_net || 0)
            return { index: i, pnl: runningPnL, time: t.exit_time }
        })
    }

    const toggleItem = (id) => {
        if (comparisonMode === 'runs') {
            setSelectedRunIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id].slice(0, 5))
        } else {
            setSelectedInstanceIds(prev => prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id].slice(0, 5))
        }
    }

    // --- DATA PREPARATION FOR RENDER ---
    const activeIds = comparisonMode === 'runs' ? selectedRunIds : selectedInstanceIds
    const activeData = comparisonMode === 'runs' ? runComparisonData : instanceComparisonData

    const chartData = useMemo(() => {
        if (activeIds.length === 0) return []

        let maxLen = 0
        activeIds.forEach(id => {
            if (activeData[id]?.equityCurve?.length > maxLen) maxLen = activeData[id].equityCurve.length
        })

        const data = []
        for (let i = 0; i < maxLen; i++) {
            const point = { index: i + 1 }
            let sumPnl = 0
            let count = 0

            activeIds.forEach(id => {
                const curve = activeData[id]?.equityCurve
                let val = null
                if (curve && curve[i]) val = curve[i].pnl
                else if (curve && curve.length > 0) val = curve[curve.length - 1].pnl

                if (val !== null) {
                    point[id] = val
                    sumPnl += val
                    count++
                }
            })

            if (activeIds.length > 1 && count > 0) {
                point['average'] = sumPnl / count
            }
            data.push(point)
        }
        return data
    }, [activeIds, activeData])

    // Average Stats for Column
    const averageStats = useMemo(() => {
        if (activeIds.length < 2) return null
        const validStats = activeIds.map(id => activeData[id]?.stats).filter(Boolean)
        if (validStats.length === 0) return null

        const avg = createEmptyStats()
        const keys = Object.keys(avg)

        validStats.forEach(s => {
            keys.forEach(k => {
                if (s[k] !== undefined) avg[k] += Number(s[k])
            })
        })
        keys.forEach(k => avg[k] = avg[k] / validStats.length)
        return avg
    }, [activeIds, activeData])

    const metrics = [
        { key: 'net_profit', label: 'Net Profit', format: (v) => `${v?.toFixed(2)}€`, colorClass: (v) => v >= 0 ? "text-success" : "text-danger" },
        { key: 'profit_factor', label: 'Profit Factor', format: (v) => v?.toFixed(2) },
        { key: 'win_rate', label: 'Win Rate', format: (v) => `${v?.toFixed(1)}%` },
        { key: 'total_trades', label: 'Trades (Avg)', format: (v) => v?.toFixed(0) },
        { key: 'max_drawdown', label: 'Max Drawdown', format: (v) => `${v?.toFixed(2)}€`, colorClass: () => "text-danger" },
        { key: 'sharpe_ratio', label: 'Sharpe', format: (v) => v?.toFixed(2) },
        { key: 'sortino_ratio', label: 'Sortino', format: (v) => v?.toFixed(2) },
    ]

    return (
        <div className="max-w-[1600px] mx-auto space-y-8 animate-fade-in pb-12">
            {/* Header / Controls */}
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                <div>
                    <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-accent to-blue-400">
                        {comparisonMode === 'runs' ? 'Run Comparison' : 'Instance Comparison'}
                    </h1>
                    <p className="text-text-secondary">
                        {comparisonMode === 'runs'
                            ? 'Compare specific backtest executions across different strategies.'
                            : 'Compare aggregated performance of different strategy configurations.'}
                    </p>
                </div>

                <div className="flex items-center gap-4">
                    {/* Mode Toggle */}
                    <div className="flex bg-slate-900/50 p-1 rounded-lg border border-slate-700/50">
                        <button
                            onClick={() => { setComparisonMode('runs'); setSelectedRunIds([]); }}
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${comparisonMode === 'runs' ? 'bg-accent text-white shadow-lg' : 'text-text-secondary hover:text-white'}`}
                        >
                            Runs
                        </button>
                        <button
                            onClick={() => { setComparisonMode('instances'); setSelectedInstanceIds([]); }}
                            className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${comparisonMode === 'instances' ? 'bg-accent text-white shadow-lg' : 'text-text-secondary hover:text-white'}`}
                        >
                            Instances
                        </button>
                    </div>

                    <div className="relative group z-20">
                        <button className="btn-primary flex items-center gap-2">
                            <Plus size={18} />
                            Add {comparisonMode === 'runs' ? 'Run' : 'Instance'}
                        </button>

                        <div className="absolute right-0 top-full mt-2 bg-slate-900 border border-slate-700 rounded-xl shadow-2xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 p-4">
                            <ComparisonSelector
                                mode={comparisonMode}
                                onSelect={(id) => toggleItem(id)}
                            />
                        </div>
                    </div>
                </div>
            </div>

            {activeIds.length === 0 ? (
                <div className="flex flex-col items-center justify-center p-20 border-2 border-dashed border-slate-700/50 rounded-2xl bg-bg-secondary/20">
                    <Layers size={48} className="text-slate-600 mb-4" />
                    <h3 className="text-xl font-semibold text-text-secondary">No {comparisonMode === 'runs' ? 'Runs' : 'Instances'} Selected</h3>
                    <p className="text-text-muted mt-2">Add items using the button above to start comparing.</p>
                </div>
            ) : (
                <>
                    {/* Metrics Matrix */}
                    <div className="bg-bg-secondary/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 overflow-x-auto shadow-xl">
                        <table className="w-full text-left border-collapse">
                            <thead>
                                <tr>
                                    <th className="p-4 border-b border-slate-700/50 text-text-secondary font-semibold min-w-[200px]">Metric</th>

                                    {/* Average Header */}
                                    {activeIds.length > 1 && (
                                        <th className="p-4 border-b border-slate-700/50 bg-white/5 min-w-[150px]">
                                            <div className="flex items-center gap-2">
                                                <div className="w-6 h-6 rounded-full bg-white/10 flex items-center justify-center">
                                                    <Sigma size={14} className="text-white" />
                                                </div>
                                                <div className="flex flex-col">
                                                    <span className="text-xs text-text-muted">Global</span>
                                                    <span className="text-sm font-bold text-white">Average</span>
                                                </div>
                                            </div>
                                        </th>
                                    )}

                                    {/* Item Headers */}
                                    {activeIds.map((id, idx) => (
                                        <th key={id} className="p-4 border-b border-slate-700/50 min-w-[150px]">
                                            <div className="flex items-center gap-2">
                                                <div
                                                    className="w-3 h-3 rounded-full"
                                                    style={{ backgroundColor: availableColors[idx % availableColors.length] }}
                                                ></div>
                                                <div className="flex flex-col">
                                                    <span className="text-xs text-text-muted">{comparisonMode === 'runs' ? 'Run' : 'Instance'}</span>
                                                    <span className="text-sm font-mono font-bold text-text-primary truncate max-w-[120px]" title={id}>
                                                        {id.split('-')[0]}...
                                                    </span>
                                                    {comparisonMode === 'instances' && activeData[id] && (
                                                        <span className="text-[10px] text-text-muted">
                                                            ({activeData[id].runCount} runs)
                                                        </span>
                                                    )}
                                                </div>
                                                <button
                                                    onClick={() => toggleItem(id)}
                                                    className="ml-auto p-1 hover:bg-white/10 rounded-full text-text-secondary hover:text-danger transition-colors"
                                                >
                                                    <X size={14} />
                                                </button>
                                            </div>
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/50">
                                {metrics.map(metric => (
                                    <tr key={metric.key} className="hover:bg-white/5 transition-colors">
                                        <td className="p-4 text-sm font-medium text-text-secondary">{metric.label}</td>

                                        {/* Average (Global) Column */}
                                        {activeIds.length > 1 && (
                                            <td className="p-4 font-mono font-bold text-white bg-white/5">
                                                {averageStats
                                                    ? metric.format(averageStats[metric.key])
                                                    : '-'
                                                }
                                            </td>
                                        )}

                                        {/* Item Columns */}
                                        {activeIds.map(id => {
                                            const stats = activeData[id]?.stats
                                            const value = stats ? stats[metric.key] : null
                                            const display = value !== null && value !== undefined ? metric.format(value) : '-'
                                            const color = metric.colorClass ? metric.colorClass(value) : 'text-text-primary'

                                            return (
                                                <td key={id} className={`p-4 font-mono font-bold ${color}`}>
                                                    {loading && !stats ? <span className="animate-pulse">...</span> : display}
                                                </td>
                                            )
                                        })}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>

                    {/* Equity Chart Overlay */}
                    <div className="bg-bg-secondary/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-xl h-[500px] flex flex-col">
                        <h3 className="text-sm text-text-secondary uppercase tracking-wider font-semibold mb-6 flex items-center gap-2">
                            <TrendingUp size={16} /> {comparisonMode === 'runs' ? 'Equity Curve Comparison' : 'Average Equity Curve Comparison'}
                        </h3>
                        <div className="flex-1 w-full min-h-0">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={chartData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                                    <XAxis
                                        dataKey="index"
                                        stroke="#94a3b8"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        label={{ value: 'Trade Index', position: 'insideBottom', offset: -5, fill: '#64748b', fontSize: 12 }}
                                    />
                                    <YAxis
                                        stroke="#94a3b8"
                                        fontSize={12}
                                        tickLine={false}
                                        axisLine={false}
                                        tickFormatter={(val) => `€${val}`}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                                        formatter={(value, name) => [`€${value.toFixed(2)}`, name]}
                                        labelFormatter={(label) => `Index #${label}`}
                                    />
                                    <Legend iconType="circle" />

                                    {/* Average Line */}
                                    {activeIds.length > 1 && (
                                        <Line
                                            type="monotone"
                                            dataKey="average"
                                            name="Global Avg"
                                            stroke="#fff"
                                            strokeDasharray="5 5"
                                            strokeWidth={2}
                                            dot={false}
                                            connectNulls
                                        />
                                    )}

                                    {/* Individual Lines */}
                                    {activeIds.map((id, idx) => (
                                        <Line
                                            key={id}
                                            type="monotone"
                                            dataKey={id}
                                            name={comparisonMode === 'runs' ? `Run ${id.split('-')[0]}` : `Inst ${id.substring(0, 6)}`}
                                            stroke={availableColors[idx % availableColors.length]}
                                            strokeWidth={2}
                                            dot={false}
                                            connectNulls
                                        />
                                    ))}
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </>
            )}
        </div>
    )
}

export default Comparison
