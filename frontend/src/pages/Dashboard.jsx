import React, { useMemo } from 'react'
import { useStrategyData } from '../hooks/useStrategyData'
import { useStrategy } from '../context/StrategyContext'
import { Sliders, Activity, DollarSign, TrendingUp, AlertTriangle } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import './Dashboard.css'

const Dashboard = () => {
    // [FIX] Separate 'executions' (raw) and 'trades' (reconstructed)
    const { executions, trades, stats, loading } = useStrategyData()
    const { runs, selectedRun, instances, selectedInstance } = useStrategy()

    const currentRun = runs.find(r => r.run_id === selectedRun)
    const currentInstance = instances.find(i => i.instance_id === selectedInstance)

    // Calculate simple metrics locally from EXECUTIONS (Volume, Fees)
    // Ensure executions is an array to avoid crash
    const safeExecutions = executions || []
    const totalExecutions = safeExecutions.length
    const totalVolume = safeExecutions.reduce((acc, curr) => acc + ((curr.price || 0) * (curr.quantity || 0)), 0)
    const fees = safeExecutions.reduce((acc, curr) => acc + (curr.fee || 0), 0)

    // Calculate Equity Curve from TRADES (Reconstructed)
    const equityCurveData = useMemo(() => {
        if (!trades || trades.length === 0) return []

        // Sort by exit time to ensure correct cumulative sum
        const sortedTrades = [...trades].sort((a, b) => new Date(a.exit_time) - new Date(b.exit_time))

        let runningPnL = 0
        return sortedTrades.map((t, i) => {
            runningPnL += (t.pnl_net || 0)
            return {
                index: i + 1,
                pnl: runningPnL,
                time: new Date(t.exit_time).toLocaleTimeString(),
                tooltipTime: new Date(t.exit_time).toLocaleString()
            }
        })
    }, [trades])


    if (loading) return <div className="loading">Loading dashboard...</div>

    // Resolve parameters from Instance (Configuration) or Run (Snapshot)
    // Priority: Run Snapshot > Instance Config
    // Note: detailed parameters are usually on the Instance.
    const parameters = currentRun?.parameters_json || currentInstance?.parameters_json;

    return (
        <div className="dashboard-container">
            {/* KPI Cards */}
            <div className="dashboard-grid">
                <div className="card">
                    <div className="card-icon"><Activity size={24} color="#38bdf8" /></div>
                    <h3>Total Trades</h3>
                    <div className="metric-value">{stats ? stats.total_trades : 0}</div>
                </div>
                <div className="card">
                    <div className="card-icon"><TrendingUp size={24} color="#4ade80" /></div>
                    <h3>Win Rate</h3>
                    <div className="metric-value">{stats ? stats.win_rate : 0}%</div>
                </div>
                <div className="card">
                    <div className="card-icon"><DollarSign size={24} color="#f87171" /></div>
                    <h3>Profit Factor</h3>
                    <div className="metric-value">{stats ? stats.profit_factor : 0}</div>
                </div>
                <div className="card">
                    <div className="card-icon"><AlertTriangle size={24} color={stats && stats.net_profit >= 0 ? "#4ade80" : "#f87171"} /></div>
                    <h3>Net PnL</h3>
                    <div className="metric-value" style={{ fontSize: '1.2rem', color: stats && stats.net_profit >= 0 ? "#4ade80" : "#f87171" }}>
                        {stats ? stats.net_profit.toFixed(2) : 0} €
                    </div>
                </div>
            </div>

            {/* Parameters Overview */}
            {parameters && (
                <div className="card parameters-card" style={{ marginTop: '2rem' }}>
                    <div className="parameters-header" style={{ marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                            <div style={{ padding: '0.5rem', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.1)' }}>
                                <Sliders size={20} className="text-accent" style={{ color: 'var(--accent)' }} />
                            </div>
                            <div>
                                <h3 style={{ margin: 0, color: 'var(--text-primary)', fontSize: '1.1rem' }}>Configuration</h3>
                                <span className="subtitle" style={{ fontSize: '0.8rem' }}>Active Strategy Parameters</span>
                            </div>
                        </div>
                    </div>

                    <div className="parameters-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
                        {Object.entries(parameters).map(([key, value]) => (
                            <div key={key} className="parameter-item" style={{
                                background: 'rgba(15, 23, 42, 0.4)',
                                padding: '1rem',
                                borderRadius: '12px',
                                border: '1px solid rgba(255,255,255,0.05)',
                                transition: 'all 0.2s ease',
                                display: 'flex',
                                flexDirection: 'column',
                                gap: '0.5rem'
                            }}>
                                <span className="parameter-key" style={{
                                    display: 'block',
                                    color: 'var(--text-secondary)',
                                    fontSize: '0.75rem',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.05em',
                                    fontWeight: '500'
                                }}>
                                    {key.replace(/_/g, ' ')}
                                </span>
                                <div className={`parameter-value ${typeof value === 'object' ? 'json' : ''}`} style={{
                                    color: 'var(--text-primary)',
                                    fontWeight: '600',
                                    fontFamily: typeof value === 'object' ? 'monospace' : 'inherit',
                                    wordBreak: 'break-all',
                                    fontSize: '1rem'
                                }}>
                                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Equity Curve Chart */}
            <div className="charts-grid" style={{ marginTop: '2rem' }}>
                <div className="card chart-card" style={{ gridColumn: '1 / -1' }}>
                    <h3>Cumulative Net Profit</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={equityCurveData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="index" stroke="#94a3b8" />
                                <YAxis domain={['auto', 'auto']} stroke="#94a3b8" />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#fff' }}
                                    labelFormatter={(label, payload) => payload[0]?.payload.tooltipTime || label}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="pnl"
                                    name="Net Profit"
                                    stroke={equityCurveData.length > 0 && equityCurveData[equityCurveData.length - 1].pnl >= 0 ? "#4ade80" : "#f87171"}
                                    strokeWidth={2}
                                    dot={false}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
