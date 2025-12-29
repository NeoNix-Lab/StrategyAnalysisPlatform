import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, Legend } from 'recharts'
import { Play, AlertTriangle, TrendingDown } from 'lucide-react'
import axios from 'axios'

const StressTest = () => {
    const [monteCarloData, setMonteCarloData] = useState(null)
    const [stressScenarios, setStressScenarios] = useState(null)
    const [loading, setLoading] = useState(false)
    const [nSimulations, setNSimulations] = useState(1000)

    const runMonteCarlo = async () => {
        setLoading(true)
        try {
            const res = await axios.get(`http://127.0.0.1:8000/api/stress/montecarlo?n_simulations=${nSimulations}`)
            setMonteCarloData(res.data)
        } catch (error) {
            console.error("Error running Monte Carlo:", error)
        } finally {
            setLoading(false)
        }
    }

    const runStressScenarios = async () => {
        setLoading(true)
        try {
            const res = await axios.get('http://127.0.0.1:8000/api/stress/stress-scenarios')
            setStressScenarios(res.data)
        } catch (error) {
            console.error("Error running stress scenarios:", error)
        } finally {
            setLoading(false)
        }
    }

    useEffect(() => {
        runMonteCarlo()
        runStressScenarios()
    }, [])

    // Prepare equity curve data with confidence bands
    const equityCurveData = monteCarloData?.equity_distribution ?
        monteCarloData.equity_distribution.p50.map((value, index) => ({
            trade: index,
            p5: monteCarloData.equity_distribution.p5[index],
            p25: monteCarloData.equity_distribution.p25[index],
            p50: value,
            p75: monteCarloData.equity_distribution.p75[index],
            p95: monteCarloData.equity_distribution.p95[index]
        })) : []

    // Prepare histogram data
    const histogramData = monteCarloData?.final_equity_histogram?.values ?
        (() => {
            const values = monteCarloData.final_equity_histogram.values
            const min = Math.min(...values)
            const max = Math.max(...values)
            const bins = 20
            const binSize = (max - min) / bins
            const histogram = Array(bins).fill(0).map((_, i) => ({
                range: `${(min + i * binSize).toFixed(0)}`,
                count: 0,
                min: min + i * binSize,
                max: min + (i + 1) * binSize
            }))

            values.forEach(val => {
                const binIndex = Math.min(Math.floor((val - min) / binSize), bins - 1)
                histogram[binIndex].count++
            })

            return histogram
        })() : []

    // Prepare stress scenarios data
    const scenariosData = stressScenarios ? [
        { name: 'Base', pnl: stressScenarios.base.net_pnl, impact: 0 },
        { name: 'Comm 2x', pnl: stressScenarios.commission_2x.net_pnl, impact: stressScenarios.commission_2x.impact },
        { name: 'Slip +1t', pnl: stressScenarios.slippage_1tick.net_pnl, impact: stressScenarios.slippage_1tick.impact },
        { name: 'Slip +2t', pnl: stressScenarios.slippage_2tick.net_pnl, impact: stressScenarios.slippage_2tick.impact },
        { name: 'No Best 10%', pnl: stressScenarios.remove_best_10pct.net_pnl, impact: stressScenarios.remove_best_10pct.impact }
    ] : []

    return (
        <div className="stress-test-container">
            <div className="stress-test-header">
                <h2>Monte Carlo & Stress Testing</h2>
                <div className="controls">
                    <div className="control-group">
                        <label>Simulations:</label>
                        <input
                            type="number"
                            value={nSimulations}
                            onChange={(e) => setNSimulations(Number(e.target.value))}
                            className="input-field-sm"
                            min="100"
                            max="10000"
                            step="100"
                        />
                    </div>
                    <button className="btn-primary" onClick={runMonteCarlo} disabled={loading}>
                        <Play size={16} /> {loading ? 'Running...' : 'Run Monte Carlo'}
                    </button>
                </div>
            </div>

            {monteCarloData && (
                <>
                    {/* Risk Metrics Cards */}
                    <div className="risk-metrics-grid">
                        <div className="card metric-card">
                            <h3>VaR 95%</h3>
                            <div className="metric-value text-danger">
                                {monteCarloData.var_95?.toFixed(2)} €
                            </div>
                            <p className="metric-desc">Worst case at 95% confidence</p>
                        </div>

                        <div className="card metric-card">
                            <h3>CVaR 95%</h3>
                            <div className="metric-value text-danger">
                                {monteCarloData.cvar_95?.toFixed(2)} €
                            </div>
                            <p className="metric-desc">Expected Shortfall</p>
                        </div>

                        <div className="card metric-card">
                            <h3>Median Final Equity</h3>
                            <div className="metric-value">
                                {monteCarloData.median_final_equity?.toFixed(2)} €
                            </div>
                            <p className="metric-desc">50th percentile outcome</p>
                        </div>

                        <div className="card metric-card">
                            <h3>Worst Drawdown (5%)</h3>
                            <div className="metric-value text-danger">
                                {monteCarloData.worst_case_drawdown?.toFixed(2)} €
                            </div>
                            <p className="metric-desc">5th percentile drawdown</p>
                        </div>
                    </div>

                    {/* Equity Curve with Confidence Bands */}
                    <div className="card chart-card" style={{ height: '500px' }}>
                        <h3>Equity Curve - Confidence Bands</h3>
                        <div className="chart-container">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={equityCurveData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis dataKey="trade" stroke="#94a3b8" />
                                    <YAxis stroke="#94a3b8" />
                                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                    <Legend />
                                    <Line type="monotone" dataKey="p95" stroke="#4ade80" strokeWidth={1} dot={false} name="95th percentile" />
                                    <Line type="monotone" dataKey="p75" stroke="#38bdf8" strokeWidth={1} dot={false} name="75th percentile" />
                                    <Line type="monotone" dataKey="p50" stroke="#fbbf24" strokeWidth={2} dot={false} name="Median" />
                                    <Line type="monotone" dataKey="p25" stroke="#f87171" strokeWidth={1} dot={false} name="25th percentile" />
                                    <Line type="monotone" dataKey="p5" stroke="#dc2626" strokeWidth={1} dot={false} name="5th percentile" />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    </div>

                    {/* Final Equity Distribution */}
                    <div className="card chart-card" style={{ height: '400px' }}>
                        <h3>Final Equity Distribution</h3>
                        <div className="chart-container">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={histogramData}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                    <XAxis dataKey="range" stroke="#94a3b8" />
                                    <YAxis stroke="#94a3b8" />
                                    <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                    <Bar dataKey="count" fill="#38bdf8" />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </div>
                </>
            )}

            {/* Stress Scenarios */}
            {stressScenarios && (
                <div className="card">
                    <div className="stress-header">
                        <AlertTriangle size={20} color="#f59e0b" />
                        <h3>Stress Test Scenarios</h3>
                    </div>

                    <div className="chart-container" style={{ height: '400px', marginTop: '1rem' }}>
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={scenariosData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="name" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                <Legend />
                                <Bar dataKey="pnl" name="Net PnL">
                                    {scenariosData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? '#4ade80' : '#f87171'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>

                    <div className="scenarios-table">
                        <table className="trades-table">
                            <thead>
                                <tr>
                                    <th>Scenario</th>
                                    <th className="text-right">Net PnL</th>
                                    <th className="text-right">Impact</th>
                                    <th className="text-right">Impact %</th>
                                </tr>
                            </thead>
                            <tbody>
                                {scenariosData.map((scenario, index) => (
                                    <tr key={index}>
                                        <td className="font-bold">{scenario.name}</td>
                                        <td className={`text-right ${scenario.pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                                            {scenario.pnl.toFixed(2)} €
                                        </td>
                                        <td className={`text-right ${scenario.impact >= 0 ? 'text-success' : 'text-danger'}`}>
                                            {scenario.impact.toFixed(2)} €
                                        </td>
                                        <td className={`text-right ${scenario.impact >= 0 ? 'text-success' : 'text-danger'}`}>
                                            {scenario.name !== 'Base' ? ((scenario.impact / stressScenarios.base.net_pnl) * 100).toFixed(1) : '0.0'}%
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}
        </div>
    )
}

export default StressTest
