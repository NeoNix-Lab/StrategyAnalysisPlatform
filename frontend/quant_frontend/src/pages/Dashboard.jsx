import React, { useMemo, useState, useEffect } from 'react'
import { useStrategyData } from '../hooks/useStrategyData'
import { useStrategy } from '../context/StrategyContext'
import { useNavigate } from 'react-router-dom'
import api from '../api/axios'
import { Sliders, Activity, DollarSign, TrendingUp, AlertTriangle, ArrowRight, Shield, Target, Zap, Waves, RefreshCw } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

const Dashboard = () => {
    // [FIX] Separate 'executions' (raw) and 'trades' (reconstructed)
    const { executions, trades, stats, loading, refresh } = useStrategyData()
    const { runs, selectedRun, instances, selectedInstance } = useStrategy()
    const navigate = useNavigate()

    const [displayCount, setDisplayCount] = useState(20)
    const [rebuilding, setRebuilding] = useState(false)

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

    const handleRebuild = async () => {
        if (!selectedRun) return
        try {
            setRebuilding(true)
            await api.post(`/trades/rebuild/${selectedRun}`)
            await refresh()
        } catch (err) {
            console.error("Rebuild failed:", err)
            alert("Failed to rebuild trades")
        } finally {
            setRebuilding(false)
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


    if (loading) return <div className="text-center mt-20 text-text-secondary animate-pulse">Loading dashboard...</div>

    // Resolve parameters from Instance (Configuration) or Run (Snapshot)
    // Priority: Run Snapshot > Instance Config
    // Note: detailed parameters are usually on the Instance.
    const parameters = currentRun?.parameters_json || currentInstance?.parameters_json;

    // Helper classes
    const cardClass = "bg-bg-secondary/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-xl transition-all hover:border-accent/30 hover:shadow-2xl hover:shadow-black/20"
    const kpiLabelClass = "text-sm text-text-secondary uppercase tracking-wider font-semibold mb-2"
    const kpiValueClass = "text-3xl font-bold text-text-primary"

    return (
        <div className="max-w-[1600px] mx-auto space-y-8 animate-fade-in">
            {/* KPI Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
                <div className={cardClass}>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-sky-500/10 rounded-lg"><Activity size={20} className="text-sky-400" /></div>
                        <h3 className={kpiLabelClass}>Total Trades</h3>
                    </div>
                    <div className={kpiValueClass}>{stats ? stats.total_trades : 0}</div>
                </div>

                <div className={cardClass}>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-green-500/10 rounded-lg"><TrendingUp size={20} className="text-green-400" /></div>
                        <h3 className={kpiLabelClass}>Win Rate</h3>
                    </div>
                    <div className={kpiValueClass}>{stats ? stats.win_rate : 0}<span className="text-lg text-text-muted ml-1">%</span></div>
                </div>

                <div className={cardClass}>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-rose-500/10 rounded-lg"><DollarSign size={20} className="text-rose-400" /></div>
                        <h3 className={kpiLabelClass}>Profit Factor</h3>
                    </div>
                    <div className={kpiValueClass}>{stats ? stats.profit_factor : 0}</div>
                </div>

                <div className={cardClass}>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-amber-500/10 rounded-lg"><AlertTriangle size={20} className={stats && stats.net_profit >= 0 ? "text-green-400" : "text-rose-400"} /></div>
                        <h3 className={kpiLabelClass}>Net PnL</h3>
                    </div>
                    <div className={`${kpiValueClass} ${stats && stats.net_profit >= 0 ? "text-success" : "text-danger"}`}>
                        {stats ? stats.net_profit.toFixed(2) : 0} <span className="text-lg opacity-70">€</span>
                    </div>
                </div>

                <div className={cardClass}>
                    <div className="flex items-center gap-3 mb-2">
                        <div className="p-2 bg-rose-500/10 rounded-lg"><DollarSign size={20} className="text-rose-300" /></div>
                        <h3 className={kpiLabelClass}>Fees</h3>
                    </div>
                    <div className="text-3xl font-bold text-rose-400">-{totalFees.toFixed(2)}€</div>
                    <div className="text-xs text-text-muted mt-1 font-mono">
                        Vol: {(stats?.total_volume || 0).toLocaleString()}
                    </div>
                </div>
            </div>

            <div className="flex justify-end relative">
                <button
                    onClick={handleRebuild}
                    disabled={rebuilding || !selectedRun}
                    className="flex items-center gap-2 px-4 py-2 bg-sky-500/10 text-sky-400 border border-sky-500/20 rounded-lg 
                    hover:bg-sky-500/20 transition-all disabled:opacity-50 disabled:cursor-not-allowed font-medium text-sm"
                >
                    <RefreshCw size={16} className={rebuilding ? "animate-spin" : ""} />
                    {rebuilding ? 'Rebuilding...' : 'Rebuild Trades'}
                </button>
            </div>

            {/* PERFORMANCE & RISK SECTION */}
            <div className="space-y-4">
                <h3 className="text-xs font-bold text-text-muted uppercase tracking-wider pl-1">Performance & Risk</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
                    <MetricCard icon={<Target size={20} className="text-violet-400" />} label="Sharpe / Sortino">
                        <MetricGroup value={stats ? stats.sharpe_ratio : 0} label="Sharpe" />
                        <div className="w-px h-8 bg-white/10 mx-4"></div>
                        <MetricGroup value={stats ? stats.sortino_ratio : 0} label="Sortino" />
                    </MetricCard>

                    <MetricCard icon={<Shield size={20} className="text-pink-400" />} label="Drawdown / Calmar">
                        <MetricGroup value={stats ? stats.max_drawdown : 0} label="MDD" isCurrency isNegative />
                        <div className="w-px h-8 bg-white/10 mx-4"></div>
                        <MetricGroup value={stats ? stats.calmar_ratio : 0} label="Calmar" />
                    </MetricCard>

                    <MetricCard icon={<Waves size={20} className="text-blue-400" />} label="Consecutive W/L">
                        <MetricGroup value={stats ? stats.max_consecutive_wins : 0} label="Wins" color="text-success" />
                        <div className="w-px h-8 bg-white/10 mx-4"></div>
                        <MetricGroup value={stats ? stats.max_consecutive_losses : 0} label="Losses" color="text-danger" />
                    </MetricCard>

                    <MetricCard icon={<Zap size={20} className="text-amber-400" />} label="Efficiency / MAE">
                        <MetricGroup value={stats ? stats.efficiency_ratio : 0} label="Eff." />
                        <div className="w-px h-8 bg-white/10 mx-4"></div>
                        <MetricGroup value={stats ? stats.avg_mae : 0} label="MAE" color="text-danger" />
                    </MetricCard>

                    <MetricCard icon={<Activity size={20} className="text-violet-400" />} label="Stability">
                        <MetricGroup
                            value={stats ? stats.stability_r2 : 0}
                            label="R²"
                            color={(stats?.stability_r2 || 0) > 0.8 ? 'text-success' : 'text-danger'}
                        />
                        <div className="w-px h-8 bg-white/10 mx-4"></div>
                        <MetricGroup value={stats ? stats.pnl_skew : 0} label="Skew" />
                    </MetricCard>
                </div>
            </div>

            {/* Parameters Overview */}
            {parameters && (
                <div className="bg-bg-secondary/30 border-l-4 border-accent rounded-r-xl p-6 backdrop-blur-sm">
                    <div className="flex items-center gap-3 mb-6 border-b border-white/5 pb-4">
                        <div className="p-2 rounded-lg bg-accent/10">
                            <Sliders size={20} className="text-accent" />
                        </div>
                        <div>
                            <h3 className="text-lg font-bold text-text-primary m-0">Configuration</h3>
                            <span className="text-xs text-text-secondary">Active Strategy Parameters</span>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                        {Object.entries(parameters).map(([key, value]) => (
                            <div key={key} className="bg-slate-900/40 border border-slate-700/50 rounded-xl p-4 hover:border-accent/30 hover:bg-sky-500/5 transition-all group">
                                <span className="block text-[10px] uppercase tracking-wider font-bold text-text-secondary mb-1 group-hover:text-accent transition-colors">
                                    {key.replace(/_/g, ' ')}
                                </span>
                                <div className={`font-mono text-sm break-all ${typeof value === 'object' ? 'text-accent' : 'text-text-primary'}`}>
                                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Equity Curve Chart */}
            <div className="grid grid-cols-1 gap-6">
                <div className={`${cardClass} h-[500px] flex flex-col`}>
                    <h3 className={kpiLabelClass}>Cumulative Net Profit</h3>
                    <div className="flex-1 w-full min-h-0">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={equityCurveData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.5} />
                                <XAxis dataKey="index" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                                <YAxis domain={['auto', 'auto']} stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(val) => `€${val}`} />
                                <Tooltip
                                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', borderRadius: '8px', color: '#fff' }}
                                    itemStyle={{ color: '#fff' }}
                                    labelFormatter={(label, payload) => payload[0]?.payload.tooltipTime || label}
                                />
                                <Line
                                    type="monotone"
                                    dataKey="pnl"
                                    name="Net Profit"
                                    stroke={equityCurveData.length > 0 && equityCurveData[equityCurveData.length - 1].pnl >= 0 ? "#4ade80" : "#f87171"}
                                    strokeWidth={3}
                                    dot={false}
                                    activeDot={{ r: 6, fill: '#fff' }}
                                />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Recent Trades Table */}
            <div className={`${cardClass} overflow-hidden flex flex-col p-0`}>
                <div className="p-6 border-b border-slate-700/50 flex justify-between items-center bg-bg-secondary/30">
                    <h3 className="text-lg font-bold text-text-primary">Recent Trades</h3>
                    <button
                        onClick={() => navigate('/trades')}
                        className="text-accent hover:text-accent-hover text-sm font-medium flex items-center gap-1 transition-colors"
                    >
                        View All <ArrowRight size={16} />
                    </button>
                </div>
                <div
                    className="overflow-auto custom-scrollbar relative"
                    onScroll={handleScroll}
                    style={{ maxHeight: '400px' }}
                >
                    <table className="w-full text-sm text-left">
                        <thead className="sticky top-0 bg-slate-900 z-10 text-xs uppercase font-semibold text-text-secondary">
                            <tr>
                                <th className="p-4 border-b border-slate-700/50">Time (Exit)</th>
                                <th className="p-4 border-b border-slate-700/50">Symbol</th>
                                <th className="p-4 border-b border-slate-700/50">Side</th>
                                <th className="p-4 border-b border-slate-700/50 text-right">Size</th>
                                <th className="p-4 border-b border-slate-700/50 text-right">Entry</th>
                                <th className="p-4 border-b border-slate-700/50 text-right">Exit</th>
                                <th className="p-4 border-b border-slate-700/50 text-right">PnL</th>
                                <th className="p-4 border-b border-slate-700/50"></th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {visibleTrades.length > 0 ? (
                                visibleTrades.map((t, i) => (
                                    <tr key={i} className="hover:bg-white/5 transition-colors">
                                        <td className="p-4 text-text-muted">{new Date(t.exit_time).toLocaleString()}</td>
                                        <td className="p-4 font-mono text-text-primary">{t.symbol}</td>
                                        <td className="p-4">
                                            <span className={`px-2 py-1 rounded text-xs font-bold ${t.side === 'BUY' ? 'bg-green-500/10 text-green-400' : 'bg-red-500/10 text-red-400'
                                                }`}>
                                                {t.side}
                                            </span>
                                        </td>
                                        <td className="p-4 text-right font-mono">{t.quantity}</td>
                                        <td className="p-4 text-right font-mono text-text-muted">{t.entry_price}</td>
                                        <td className="p-4 text-right font-mono text-text-muted">{t.exit_price}</td>
                                        <td className={`p-4 text-right font-mono font-bold ${t.pnl_net >= 0 ? 'text-green-400' : 'text-red-400'
                                            }`}>
                                            {t.pnl_net.toFixed(2)}
                                        </td>
                                        <td className="p-4 text-right">
                                            <button
                                                className="p-1.5 rounded-lg text-text-muted hover:bg-white/10 hover:text-white transition-all"
                                                title="Replay Trade"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    navigate(`/trades/${t.trade_id}/replay`);
                                                }}
                                            >
                                                <Activity size={16} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan="8" className="p-8 text-center text-text-muted">No trades recorded</td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

// Subcomponents for cleaner JSX
const MetricCard = ({ icon, label, children }) => (
    <div className="bg-bg-secondary/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-lg">
        <div className="flex justify-center mb-3">{icon}</div>
        <div className="text-center text-xs text-text-secondary uppercase tracking-wider font-semibold mb-4">{label}</div>
        <div className="flex justify-between items-center">
            {children}
        </div>
    </div>
)

const MetricGroup = ({ value, label, color = "text-text-primary", isCurrency = false, isNegative = false }) => (
    <div className="flex flex-col items-center flex-1">
        <span className={`text-xl font-bold ${color}`}>
            {value}
            {isCurrency && <span className="text-sm opacity-70 ml-0.5">€</span>}
        </span>
        <span className="text-[10px] text-text-muted uppercase mt-1">{label}</span>
    </div>
)

export default Dashboard

