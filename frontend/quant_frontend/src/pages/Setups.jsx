import { useState, useEffect } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, PieChart, Pie, Legend } from 'recharts'
import { Tag, TrendingUp, Award } from 'lucide-react'
import api from '../api/axios'

const Setups = () => {
    const [setupStats, setSetupStats] = useState([])
    const [loading, setLoading] = useState(false)

    useEffect(() => {
        fetchSetupAnalysis()
    }, [])

    const fetchSetupAnalysis = async () => {
        setLoading(true)
        try {
            const res = await api.get('/setups/setup-analysis')
            setSetupStats(res.data)
        } catch (error) {
            console.error("Error fetching setup analysis:", error)
        } finally {
            setLoading(false)
        }
    }

    if (loading) return <div className="loading">Loading setup analysis...</div>

    // Best and worst setups
    const bestSetup = setupStats.length > 0 ? setupStats[0] : null
    const worstSetup = setupStats.length > 0 ? setupStats[setupStats.length - 1] : null

    // Prepare pie chart data
    const pieData = setupStats.map(s => ({
        name: s.setup,
        value: s.count
    }))

    const COLORS = ['#4ade80', '#38bdf8', '#fbbf24', '#f87171', '#818cf8', '#fb923c']

    return (
        <div className="setups-container">
            <div className="setups-header">
                <h2>Setup & Pattern Analysis</h2>
                <Tag size={24} color="#38bdf8" />
            </div>

            {bestSetup && worstSetup && (
                <div className="best-worst-grid">
                    <div className="card best-setup-card">
                        <div className="setup-card-header">
                            <Award size={20} color="#4ade80" />
                            <h3>Best Setup</h3>
                        </div>
                        <div className="setup-card-content">
                            <div className="setup-name">{bestSetup.setup}</div>
                            <div className="setup-metrics">
                                <div className="setup-metric">
                                    <span className="label">Total PnL</span>
                                    <span className="value text-success">{bestSetup.total_pnl.toFixed(2)} €</span>
                                </div>
                                <div className="setup-metric">
                                    <span className="label">Win Rate</span>
                                    <span className="value">{bestSetup.win_rate.toFixed(1)}%</span>
                                </div>
                                <div className="setup-metric">
                                    <span className="label">Profit Factor</span>
                                    <span className="value">{bestSetup.profit_factor.toFixed(2)}</span>
                                </div>
                                <div className="setup-metric">
                                    <span className="label">Trades</span>
                                    <span className="value">{bestSetup.count}</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="card worst-setup-card">
                        <div className="setup-card-header">
                            <TrendingUp size={20} color="#f87171" style={{ transform: 'rotate(180deg)' }} />
                            <h3>Worst Setup</h3>
                        </div>
                        <div className="setup-card-content">
                            <div className="setup-name">{worstSetup.setup}</div>
                            <div className="setup-metrics">
                                <div className="setup-metric">
                                    <span className="label">Total PnL</span>
                                    <span className={`value ${worstSetup.total_pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                                        {worstSetup.total_pnl.toFixed(2)} €
                                    </span>
                                </div>
                                <div className="setup-metric">
                                    <span className="label">Win Rate</span>
                                    <span className="value">{worstSetup.win_rate.toFixed(1)}%</span>
                                </div>
                                <div className="setup-metric">
                                    <span className="label">Profit Factor</span>
                                    <span className="value">{worstSetup.profit_factor.toFixed(2)}</span>
                                </div>
                                <div className="setup-metric">
                                    <span className="label">Trades</span>
                                    <span className="value">{worstSetup.count}</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="charts-grid">
                {/* Performance by Setup */}
                <div className="card chart-card">
                    <h3>Performance by Setup</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={setupStats}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="setup" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                <Legend />
                                <Bar dataKey="total_pnl" name="Total PnL (€)">
                                    {setupStats.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.total_pnl >= 0 ? '#4ade80' : '#f87171'} />
                                    ))}
                                </Bar>
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Trade Distribution */}
                <div className="card chart-card">
                    <h3>Trade Distribution by Setup</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <PieChart>
                                <Pie
                                    data={pieData}
                                    cx="50%"
                                    cy="50%"
                                    labelLine={false}
                                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                                    outerRadius={120}
                                    fill="#8884d8"
                                    dataKey="value"
                                >
                                    {pieData.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                    ))}
                                </Pie>
                                <Tooltip />
                            </PieChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Detailed Table */}
            <div className="card">
                <h3>Setup Performance Details</h3>
                <div className="table-container">
                    <table className="trades-table">
                        <thead>
                            <tr>
                                <th>Setup</th>
                                <th className="text-right">Trades</th>
                                <th className="text-right">Win Rate</th>
                                <th className="text-right">Profit Factor</th>
                                <th className="text-right">Avg Trade</th>
                                <th className="text-right">Total PnL</th>
                            </tr>
                        </thead>
                        <tbody>
                            {setupStats.map((setup, index) => (
                                <tr key={index} className="trade-row">
                                    <td className="font-bold">{setup.setup}</td>
                                    <td className="text-right">{setup.count}</td>
                                    <td className="text-right">{setup.win_rate.toFixed(1)}%</td>
                                    <td className="text-right">{setup.profit_factor.toFixed(2)}</td>
                                    <td className={`text-right ${setup.avg_trade >= 0 ? 'text-success' : 'text-danger'}`}>
                                        {setup.avg_trade.toFixed(2)} €
                                    </td>
                                    <td className={`text-right font-bold ${setup.total_pnl >= 0 ? 'text-success' : 'text-danger'}`}>
                                        {setup.total_pnl.toFixed(2)} €
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <div className="card">
                <h3>Recommendations</h3>
                <div className="recommendations">
                    {bestSetup && (
                        <div className="recommendation success">
                            <strong>✓ Focus on "{bestSetup.setup}"</strong> - This setup has the best performance with {bestSetup.total_pnl.toFixed(2)}€ total profit.
                        </div>
                    )}
                    {worstSetup && worstSetup.total_pnl < 0 && (
                        <div className="recommendation warning">
                            <strong>⚠ Avoid "{worstSetup.setup}"</strong> - This setup is losing money. Consider removing it from your strategy.
                        </div>
                    )}
                    {setupStats.filter(s => s.win_rate < 40).length > 0 && (
                        <div className="recommendation info">
                            <strong>ℹ Low Win Rate Setups</strong> - {setupStats.filter(s => s.win_rate < 40).length} setup(s) have win rate below 40%. Review their logic.
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default Setups
