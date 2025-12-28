import React, { useState, useMemo } from 'react'
import { useStrategy } from '../context/StrategyContext'
import axios from 'axios'
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, LineChart, Line, Legend } from 'recharts'
import { Check, X, TrendingUp, Activity, BarChart2 } from 'lucide-react'

const CompareRuns = () => {
    const { runs, instances, selectedInstance } = useStrategy()
    const [selectedRunIds, setSelectedRunIds] = useState([])
    const [comparisonData, setComparisonData] = useState([])
    const [loading, setLoading] = useState(false)

    // Scatter Plot Config
    const [xAxisParam, setXAxisParam] = useState('learning_rate') // Default, will be dynamic
    const [yAxisMetric, setYAxisMetric] = useState('net_profit')

    // Toggle Selection
    const toggleRun = (runId) => {
        setSelectedRunIds(prev =>
            prev.includes(runId)
                ? prev.filter(id => id !== runId)
                : [...prev, runId]
        )
    }

    const handleCompare = async () => {
        if (selectedRunIds.length === 0) return
        setLoading(true)
        try {
            const res = await axios.post('http://127.0.0.1:8000/api/metrics/compare', {
                run_ids: selectedRunIds
            })
            setComparisonData(res.data)
        } catch (err) {
            console.error("Comparison failed", err)
        } finally {
            setLoading(false)
        }
    }

    // Prepare Data for Scatter Plot
    const scatterData = useMemo(() => {
        if (!comparisonData.length) return []

        return comparisonData.map(metrics => {
            const run = runs.find(r => r.run_id === metrics.run_id)
            const params = run?.parameters_json || {}

            // Try to resolve nested params if needed, or flat
            // For ML, params might be in 'process' or 'model' keys if flattened, 
            // but usually we store flat key-values in parameters_json for runs.

            return {
                run_id: metrics.run_id,
                x: Number(params[xAxisParam] || 0),
                y: Number(metrics[yAxisMetric] || 0),
                params: params
            }
        })
    }, [comparisonData, runs, xAxisParam, yAxisMetric])

    // Prepare Data for Equity Curve Overlay
    // We need to normalize time or index. 
    // Option A: By Trade Count (Index) - easier to overlay.
    const equityOverlayData = useMemo(() => {
        if (!comparisonData.length) return []

        // Find max length
        let maxTrades = 0
        comparisonData.forEach(c => {
            if (c.equity_curve && c.equity_curve.length > maxTrades) {
                maxTrades = c.equity_curve.length
            }
        })

        const data = []
        for (let i = 0; i < maxTrades; i++) {
            const point = { index: i + 1 }
            comparisonData.forEach(c => {
                if (c.equity_curve && c.equity_curve[i]) {
                    point[c.run_id] = c.equity_curve[i].pnl
                }
            })
            data.push(point)
        }
        return data
    }, [comparisonData])

    // Available Parameters (extract keys from first selected run)
    const availableParams = useMemo(() => {
        if (selectedRunIds.length === 0) return []
        const firstRun = runs.find(r => r.run_id === selectedRunIds[0])
        return firstRun?.parameters_json ? Object.keys(firstRun.parameters_json) : []
    }, [selectedRunIds, runs])

    return (
        <div className="p-6 text-slate-200">
            <header className="mb-8">
                <h1 className="text-2xl font-bold text-white mb-2 flex items-center gap-2">
                    <BarChart2 className="text-accent" /> Strategy Comparison
                </h1>
                <p className="text-slate-400">Compare multiple runs to analyze parameter sensitivity and performance stability.</p>
            </header>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

                {/* LEFT: Run Selection Panel */}
                <div className="card lg:col-span-1 h-[calc(100vh-200px)] overflow-hidden flex flex-col">
                    <div className="p-4 border-b border-white/10 flex justify-between items-center">
                        <h3 className="font-semibold">Available Runs ({runs.length})</h3>
                        <span className="text-xs text-slate-500">{selectedInstance}</span>
                    </div>
                    <div className="overflow-y-auto flex-1 p-2 space-y-1">
                        {runs.map(run => {
                            const isSelected = selectedRunIds.includes(run.run_id)
                            return (
                                <div
                                    key={run.run_id}
                                    onClick={() => toggleRun(run.run_id)}
                                    className={`p-3 rounded-lg cursor-pointer transition-all border ${isSelected
                                            ? 'bg-accent/10 border-accent text-white'
                                            : 'bg-slate-800/50 border-transparent hover:bg-slate-800 text-slate-400'
                                        }`}
                                >
                                    <div className="flex justify-between items-start">
                                        <span className="text-xs font-mono opacity-50">{run.run_id.slice(0, 8)}</span>
                                        {isSelected && <Check size={14} className="text-accent" />}
                                    </div>
                                    <div className="text-sm font-medium mt-1">
                                        {new Date(run.start_utc).toLocaleString()}
                                    </div>
                                    {run.metrics_json && (
                                        <div className="flex gap-3 mt-2 text-xs">
                                            <span className={run.metrics_json.net_profit >= 0 ? "text-green-400" : "text-red-400"}>
                                                {run.metrics_json.net_profit?.toFixed(2)}€
                                            </span>
                                            <span className="text-slate-500">PF: {run.metrics_json.profit_factor}</span>
                                        </div>
                                    )}
                                </div>
                            )
                        })}
                    </div>
                    <div className="p-4 border-t border-white/10">
                        <button
                            onClick={handleCompare}
                            disabled={selectedRunIds.length < 2 || loading}
                            className={`w-full py-2 px-4 rounded font-semibold transition-all ${selectedRunIds.length < 2
                                    ? 'bg-slate-700 text-slate-500 cursor-not-allowed'
                                    : 'bg-accent hover:bg-accent-hover text-white'
                                }`}
                        >
                            {loading ? 'Analyzing...' : `Compare ${selectedRunIds.length} Runs`}
                        </button>
                    </div>
                </div>

                {/* RIGHT: Charts */}
                <div className="lg:col-span-2 space-y-6 overflow-y-auto h-[calc(100vh-200px)]">

                    {/* 1. Parameter Sensitivity */}
                    {comparisonData.length > 0 && (
                        <div className="card">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="flex items-center gap-2"><Activity size={18} /> Parameter Sensitivity</h3>
                                <div className="flex gap-2">
                                    <select
                                        className="bg-slate-900 border border-white/10 rounded px-2 py-1 text-sm"
                                        value={xAxisParam}
                                        onChange={(e) => setXAxisParam(e.target.value)}
                                    >
                                        <option value="">Select Parameter (X)</option>
                                        {availableParams.map(p => <option key={p} value={p}>{p}</option>)}
                                    </select>
                                    <select
                                        className="bg-slate-900 border border-white/10 rounded px-2 py-1 text-sm"
                                        value={yAxisMetric}
                                        onChange={(e) => setYAxisMetric(e.target.value)}
                                    >
                                        <option value="net_profit">Net Profit</option>
                                        <option value="profit_factor">Profit Factor</option>
                                        <option value="sharpe_ratio">Sharpe Ratio</option>
                                        <option value="max_drawdown">Max Drawdown</option>
                                        <option value="win_rate">Win Rate</option>
                                    </select>
                                </div>
                            </div>
                            <div className="h-[300px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis
                                            type="number"
                                            dataKey="x"
                                            name={xAxisParam}
                                            stroke="#94a3b8"
                                            label={{ value: xAxisParam, position: 'bottom', fill: '#94a3b8' }}
                                        />
                                        <YAxis
                                            type="number"
                                            dataKey="y"
                                            name={yAxisMetric}
                                            stroke="#94a3b8"
                                            label={{ value: yAxisMetric, angle: -90, position: 'left', fill: '#94a3b8' }}
                                        />
                                        <Tooltip
                                            cursor={{ strokeDasharray: '3 3' }}
                                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff' }}
                                            formatter={(value, name, props) => [value, name === 'x' ? xAxisParam : yAxisMetric]}
                                        />
                                        <Scatter name="Runs" data={scatterData} fill="#38bdf8" />
                                    </ScatterChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {/* 2. Equity Curve Overlay */}
                    {comparisonData.length > 0 && (
                        <div className="card">
                            <h3 className="flex items-center gap-2 mb-4"><TrendingUp size={18} /> Equity Curve Overlay</h3>
                            <div className="h-[400px]">
                                <ResponsiveContainer width="100%" height="100%">
                                    <LineChart data={equityOverlayData}>
                                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                        <XAxis dataKey="index" stroke="#94a3b8" label={{ value: 'Trade Index', position: 'bottom', fill: '#64748b' }} />
                                        <YAxis stroke="#94a3b8" />
                                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                        <Legend />
                                        {comparisonData.map((run, i) => (
                                            <Line
                                                key={run.run_id}
                                                type="monotone"
                                                dataKey={run.run_id}
                                                name={`Run ${run.run_id.slice(0, 6)}`}
                                                stroke={`hsl(${i * 60}, 70%, 50%)`}
                                                dot={false}
                                                strokeWidth={2}
                                            />
                                        ))}
                                    </LineChart>
                                </ResponsiveContainer>
                            </div>
                        </div>
                    )}

                    {!comparisonData.length && !loading && (
                        <div className="flex flex-col items-center justify-center h-64 text-slate-500 border border-dashed border-slate-700 rounded-lg">
                            <BarChart2 size={48} className="mb-4 opacity-50" />
                            <p>Select at least 2 runs and click Compare to analyze results.</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default CompareRuns
