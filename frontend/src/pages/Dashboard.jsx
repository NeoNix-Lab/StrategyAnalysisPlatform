import React, { useMemo, useState, useEffect } from 'react'
import { useStrategyData } from '../hooks/useStrategyData'
import { useStrategy } from '../context/StrategyContext'
import { useNavigate } from 'react-router-dom'
import { Sliders, Activity, DollarSign, TrendingUp, AlertTriangle, ArrowRight, Shield, Target, Zap, Waves } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import './Dashboard.css'

const Dashboard = () => {
    // [FIX] Separate 'executions' (raw) and 'trades' (reconstructed)
    const { executions, trades, stats, loading } = useStrategyData()
    const { runs, selectedRun, instances, selectedInstance } = useStrategy()
    const navigate = useNavigate()

    const [displayCount, setDisplayCount] = useState(20)

    // Reset display count when run changes
    useEffect(() => {
        setDisplayCount(20)
    }, [selectedRun])

    const sortedTrades = useMemo(() => {
        if (!trades) return []
        return [...trades].sort((a, b) => new Date(b.exit_time) - new Date(a.exit_time))
    }, [trades])

    const visibleTrades = useMemo(() => {
        return sortedTrades.slice(0, displayCount)
    }, [sortedTrades, displayCount])

    const handleScroll = (e) => {
        const { scrollTop, clientHeight, scrollHeight } = e.target
        // Load more when near bottom (50px threshold)
        if (scrollHeight - scrollTop <= clientHeight + 50) {
            if (displayCount < sortedTrades.length) {
                setDisplayCount(prev => prev + 20)
            }
        }
    }

    const currentRun = runs.find(r => r.run_id === selectedRun)
    const currentInstance = instances.find(i => i.instance_id === selectedInstance)

    // Calculate simple metrics locally from EXECUTIONS (Volume, Fees)
    // Ensure executions is an array to avoid crash
    const safeExecutions = executions || []

    // Prefer backend stats for fees, fallback to local sum
    const totalFees = stats?.total_fees !== undefined
        ? stats.total_fees
        : safeExecutions.reduce((acc, curr) => acc + (curr.fee || 0), 0)

    // Calculate Equity Curve: Prefer Backend -> Fallback to Local
    const equityCurveData = useMemo(() => {
        // 1. Backend Source
        if (stats?.equity_curve && stats.equity_curve.length > 0) {
            return stats.equity_curve.map((point, i) => ({
                ...point,
                index: i + 1,
                // Ensure time is parseable
                tooltipTime: new Date(point.time).toLocaleString(),
                // Backend provides 'pnl' (cumulative) and 'drawdown'
            }))
        }

        // 2. Local Fallback (Reconstruction)
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
    }, [stats, trades])


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
                <div className="card">
                    <div className="card-icon"><DollarSign size={24} color="#fca5a5" /></div>
                    <h3>Fees</h3>
                    <div className="metric-value" style={{ color: '#f87171' }}>-{totalFees.toFixed(2)}€</div>
                    <div style={{ fontSize: '0.8rem', color: '#64748b', marginTop: '0.25rem' }}>
                        Vol: {(stats?.total_volume || 0).toLocaleString()}
                    </div>
                </div>
            </div>

            {/* PERFORMANCE & RISK SECTION */}
            <h3 style={{ marginTop: '2rem', marginBottom: '1rem', color: '#94a3b8', fontSize: '0.9rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Performance & Risk</h3>
            <div className="dashboard-grid">
                {/* Card 1: Risk Adjusted Returns */}
                <div className="card">
                    <div className="card-icon"><Target size={24} color="#a78bfa" /></div>
                    <div className="metric-label">Sharpe / Sortino</div>
                    <div className="metric-value-group">
                        <div title="Sharpe Ratio">
                            <span className="value">{stats ? stats.sharpe_ratio : 0}</span>
                            <span className="sub-label">Sharpe</span>
                        </div>
                        <div className="divider"></div>
                        <div title="Sortino Ratio">
                            <span className="value">{stats ? stats.sortino_ratio : 0}</span>
                            <span className="sub-label">Sortino</span>
                        </div>
                    </div>
                </div>

                {/* Card 2: Drawdown & Recovery */}
                <div className="card">
                    <div className="card-icon"><Shield size={24} color="#f472b6" /></div>
                    <div className="metric-label">Drawdown / Calmar</div>
                    <div className="metric-value-group">
                        <div title="Max Drawdown">
                            <span className="value" style={{ color: '#f87171' }}>{stats ? stats.max_drawdown : 0}€</span>
                            <span className="sub-label">MDD</span>
                        </div>
                        <div className="divider"></div>
                        <div title="Calmar Ratio">
                            <span className="value">{stats ? stats.calmar_ratio : 0}</span>
                            <span className="sub-label">Calmar</span>
                        </div>
                    </div>
                </div>

                {/* Card 3: Streaks */}
                <div className="card">
                    <div className="card-icon"><Waves size={24} color="#60a5fa" /></div>
                    <div className="metric-label">Consecutive W/L</div>
                    <div className="metric-value-group">
                        <div title="Max Consecutive Wins">
                            <span className="value" style={{ color: '#4ade80' }}>{stats ? stats.max_consecutive_wins : 0}</span>
                            <span className="sub-label">Wins</span>
                        </div>
                        <div className="divider"></div>
                        <div title="Max Consecutive Losses">
                            <span className="value" style={{ color: '#f87171' }}>{stats ? stats.max_consecutive_losses : 0}</span>
                            <span className="sub-label">Losses</span>
                        </div>
                    </div>
                </div>

                {/* Card 4: Efficiency & Execution */}
                <div className="card">
                    <div className="card-icon"><Zap size={24} color="#fbbf24" /></div>
                    <div className="metric-label">Efficiency / MAE</div>
                    <div className="metric-value-group">
                        <div title="Efficiency Ratio">
                            <span className="value">{stats ? stats.efficiency_ratio : 0}</span>
                            <span className="sub-label">Eff.</span>
                        </div>
                        <div className="divider"></div>
                        <div title="Average MAE">
                            <span className="value" style={{ color: '#f87171' }}>{stats ? stats.avg_mae : 0}</span>
                            <span className="sub-label">MAE</span>
                        </div>
                    </div>
                </div>

                {/* Card 5: Stability */}
                <div className="card">
                    <div className="card-icon"><Activity size={24} color="#a78bfa" /></div>
                    <div className="metric-label">Stability (Level 4)</div>
                    <div className="metric-value-group">
                        <div title="R-Squared (Linearity)">
                            <span className="value" style={{ color: (stats?.stability_r2 || 0) > 0.8 ? '#4ade80' : '#f87171' }}>
                                {stats ? stats.stability_r2 : 0}
                            </span>
                            <span className="sub-label">R²</span>
                        </div>
                        <div className="divider"></div>
                        <div title="PnL Skewness">
                            <span className="value">{stats ? stats.pnl_skew : 0}</span>
                            <span className="sub-label">Skew</span>
                        </div>
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

            {/* Recent Trades Table */}
            <div className="card" style={{ marginTop: '2rem' }}>
                <div className="card-header" style={{ marginBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <h3 style={{ margin: 0 }}>Recent Trades</h3>
                    <button
                        onClick={() => navigate('/trades')}
                        style={{
                            background: 'transparent',
                            border: 'none',
                            color: '#3b82f6',
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.5rem',
                            fontSize: '0.9rem',
                            padding: '0.5rem',
                            transition: 'color 0.2s'
                        }}
                        onMouseEnter={(e) => e.target.style.color = '#60a5fa'}
                        onMouseLeave={(e) => e.target.style.color = '#3b82f6'}
                    >
                        View All <ArrowRight size={16} />
                    </button>
                </div>
                <div
                    className="table-container infinite-scroll-container"
                    onScroll={handleScroll}
                    style={{
                        overflowX: 'auto',
                        overflowY: 'auto',
                        maxHeight: '400px', // Fixed height for scroll
                        position: 'relative'
                    }}
                >
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                        <thead style={{ position: 'sticky', top: 0, background: '#0f172a', zIndex: 10 }}>
                            <tr style={{ borderBottom: '1px solid #334155', textAlign: 'left', color: '#94a3b8' }}>
                                <th style={{ padding: '0.75rem' }}>Time (Exit)</th>
                                <th style={{ padding: '0.75rem' }}>Symbol</th>
                                <th style={{ padding: '0.75rem' }}>Side</th>
                                <th style={{ padding: '0.75rem', textAlign: 'right' }}>Size</th>
                                <th style={{ padding: '0.75rem', textAlign: 'right' }}>Entry</th>
                                <th style={{ padding: '0.75rem', textAlign: 'right' }}>Exit</th>
                                <th style={{ padding: '0.75rem', textAlign: 'right' }}>PnL</th>
                            </tr>
                        </thead>
                        <tbody>
                            {visibleTrades.length > 0 ? (
                                visibleTrades.map((t, i) => (
                                    <tr key={i} style={{ borderBottom: '1px solid #1e293b' }}>
                                        <td style={{ padding: '0.75rem' }}>{new Date(t.exit_time).toLocaleString()}</td>
                                        <td style={{ padding: '0.75rem' }}>{t.symbol}</td>
                                        <td style={{ padding: '0.75rem' }}>
                                            <span style={{
                                                color: t.side === 'BUY' ? '#4ade80' : '#f87171',
                                                background: t.side === 'BUY' ? 'rgba(74, 222, 128, 0.1)' : 'rgba(248, 113, 113, 0.1)',
                                                padding: '0.25rem 0.5rem',
                                                borderRadius: '4px',
                                                fontSize: '0.8rem'
                                            }}>
                                                {t.side}
                                            </span>
                                        </td>
                                        <td style={{ padding: '0.75rem', textAlign: 'right' }}>{t.quantity}</td>
                                        <td style={{ padding: '0.75rem', textAlign: 'right' }}>{t.entry_price}</td>
                                        <td style={{ padding: '0.75rem', textAlign: 'right' }}>{t.exit_price}</td>
                                        <td style={{ padding: '0.75rem', textAlign: 'right', fontWeight: 'bold', color: t.pnl_net >= 0 ? '#4ade80' : '#f87171' }}>
                                            {t.pnl_net.toFixed(2)}
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="7" style={{ padding: '1rem', textAlign: 'center', color: '#64748b' }}>No trades recorded</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

export default Dashboard
