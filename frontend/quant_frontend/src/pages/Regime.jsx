import { Fragment, useMemo, useState } from 'react'
import { useStrategyData } from '../hooks/useStrategyData'
import { useStrategy } from '../context/StrategyContext'
import api from '../api/axios'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell, FunnelChart } from 'recharts'

const Regime = () => {
    const { trades, loading, refresh, regimePerformance } = useStrategyData()
    const { selectedRun } = useStrategy()
    const [rebuilding, setRebuilding] = useState(false)
    const [rebuildError, setRebuildError] = useState(null)

    const triggerRebuild = async () => {
        if (!selectedRun) return
        setRebuilding(true)
        setRebuildError(null)
        try {
            await api.post(`/regime/${selectedRun}/rebuild`)
            await refresh()
        } catch (err) {
            const detail = err?.response?.data?.detail
            setRebuildError(detail || err.message || 'Errore sconosciuto')
        } finally {
            setRebuilding(false)
        }
    }

    const fallbackRegimeStats = useMemo(() => {
        if (!trades.length) return { trend: [], volatility: [], matrix: {} }

        const calculateMetrics = (subset) => {
            const total = subset.length
            if (total === 0) return { pnl: 0, winRate: 0, count: 0, pf: 0 }

            const wins = subset.filter(t => t.pnl_net > 0)
            const losses = subset.filter(t => t.pnl_net <= 0)
            const totalWin = wins.reduce((sum, t) => sum + t.pnl_net, 0)
            const totalLoss = Math.abs(losses.reduce((sum, t) => sum + t.pnl_net, 0))

            return {
                pnl: subset.reduce((sum, t) => sum + t.pnl_net, 0),
                winRate: (wins.length / total) * 100,
                count: total,
                pf: totalLoss === 0 ? totalWin : totalWin / totalLoss
            }
        }

        const trends = ['BULL', 'BEAR', 'RANGE']
        const trendStats = trends.map(trend => {
            const subset = trades.filter(t => t.regime_trend === trend)
            return { name: trend, ...calculateMetrics(subset) }
        })

        const vols = ['HIGH', 'LOW', 'NORMAL']
        const volStats = vols.map(vol => {
            const subset = trades.filter(t => t.regime_volatility === vol)
            return { name: vol, ...calculateMetrics(subset) }
        })

        const matrix = {}
        trends.forEach(trend => {
            vols.forEach(vol => {
                const subset = trades.filter(t => t.regime_trend === trend && t.regime_volatility === vol)
                matrix[`${trend}_${vol}`] = calculateMetrics(subset)
            })
        })

        return { trend: trendStats, volatility: volStats, matrix }
    }, [trades])

    const regimeStats = regimePerformance || fallbackRegimeStats

    if (loading) return <div className="loading">Loading regime analysis...</div>

    const getMatrixColor = (pnl) => {
        if (pnl > 0) return 'rgba(74, 222, 128, 0.2)' // Success light
        if (pnl < 0) return 'rgba(248, 113, 113, 0.2)' // Danger light
        return 'transparent'
    }

    return (
        <div className="regime-container">
            <div className="regime-actions">
                <button
                    type="button"
                    className="btn-primary"
                    disabled={!selectedRun || rebuilding}
                    onClick={triggerRebuild}
                >
                    {rebuilding ? 'Ricalcolo in corso…' : 'Ricalcola regime'}
                </button>
                {rebuildError && <span className="text-danger ml-2">{rebuildError}</span>}
            </div>
            {/* Charts Row */}
            <div className="charts-grid">
                <div className="card chart-card">
                    <h3>Performance by Trend</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={regimeStats.trend}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="name" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                <Legend />
                                <Bar dataKey="pnl" name="Net Profit (€)" fill="#38bdf8">
                                    {regimeStats.trend.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? '#4ade80' : '#f87171'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                <div className="card chart-card">
                    <h3>Performance by Volatility</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={regimeStats.volatility}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="name" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                <Legend />
                                <Bar dataKey="pnl" name="Net Profit (€)" fill="#818cf8">
                                    {regimeStats.volatility.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? '#4ade80' : '#f87171'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            <div className='test-flowchart'>
                <h3>Test</h3>
                <ResponsiveContainer width="100%" height="100%">
                    <h3>Test</h3>

                    {/* <FunnelChart data={regimeStats.volatility}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis dataKey="name" stroke="#94a3b8" />
                        <YAxis stroke="#94a3b8" />
                        <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                        <Legend />
                        <Bar dataKey="pnl" name="Net Profit (€)" fill="#818cf8">
                            {regimeStats.volatility.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.pnl >= 0 ? '#4ade80' : '#f87171'} />
                            ))}
                        </Bar>

                    </FunnelChart> */}
                </ResponsiveContainer>
            </div>

            {/* Matrix View */}
            <div className="card" style={{ marginTop: '1.5rem' }}>
                <h3>Regime Matrix (Net Profit)</h3>
                <div className="matrix-grid">
                    <div className="matrix-header"></div>
                    <div className="matrix-header">HIGH VOL</div>
                    <div className="matrix-header">NORMAL VOL</div>
                    <div className="matrix-header">LOW VOL</div>

                    {['BULL', 'BEAR', 'RANGE'].map(trend => (
                        <Fragment key={trend}>
                            <div className="matrix-row-header">{trend}</div>
                            {['HIGH', 'NORMAL', 'LOW'].map(vol => {
                                const data = regimeStats.matrix[`${trend}_${vol}`]
                                return (
                                    <div
                                        key={`${trend}_${vol}`}
                                        className="matrix-cell"
                                        style={{ backgroundColor: getMatrixColor(data?.pnl || 0) }}
                                    >
                                        <div className={`matrix-value ${data?.pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                                            {data?.pnl ? data.pnl.toFixed(2) : 0} €
                                        </div>
                                        <div className="matrix-sub">
                                            {data?.count || 0} trades
                                        </div>
                                    </div>
                                )
                            })}
                        </Fragment>
                    ))}
                </div>
            </div>
        </div>
    )
}

export default Regime
