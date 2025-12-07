import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import { useStrategyData } from '../hooks/useStrategyData'
import { useStrategy } from '../context/StrategyContext'
import { Sliders } from 'lucide-react'
import './Dashboard.css'

const Dashboard = () => {
    const { stats, trades, loading } = useStrategyData()
    const { runs, selectedRun } = useStrategy()

    const currentRun = runs.find(r => r.run_id === selectedRun)

    const CustomTooltip = ({ active, payload, label }) => {
        if (active && payload && payload.length) {
            return (
                <div className="custom-tooltip">
                    <p className="label">{`Trade #${label}`}</p>
                    <p className="value" style={{ color: '#38bdf8' }}>
                        {`Equity: ${payload[0].value.toFixed(2)} €`}
                    </p>
                </div>
            )
        }
        return null
    }

    if (loading) return <div className="loading">Loading dashboard...</div>

    return (
        <div className="dashboard-container">
            {/* KPI Cards */}
            <div className="dashboard-grid">
                <div className="card">
                    <h3>Net Profit</h3>
                    <div className={`metric-value ${stats?.net_profit < 0 ? 'negative' : ''}`}>
                        {stats?.net_profit} €
                    </div>
                </div>
                <div className="card">
                    <h3>Win Rate</h3>
                    <div className="metric-value">{stats?.win_rate}%</div>
                </div>
                <div className="card">
                    <h3>Profit Factor</h3>
                    <div className="metric-value">{stats?.profit_factor}</div>
                </div>
                <div className="card">
                    <h3>Max Drawdown</h3>
                    <div className="metric-value negative">{stats?.max_drawdown} €</div>
                </div>
            </div>

            {/* Parameters Overview */}
            {currentRun?.parameters && (
                <div className="card parameters-card">
                    <div className="parameters-header">
                        <Sliders size={20} className="text-accent" style={{ color: 'var(--accent)' }} />
                        <h3>Run Configuration</h3>
                    </div>
                    <div className="parameters-grid">
                        {Object.entries(currentRun.parameters).map(([key, value]) => (
                            <div key={key} className="parameter-item">
                                <span className="parameter-key">{key.replace(/_/g, ' ')}</span>
                                <div className={`parameter-value ${typeof value === 'object' ? 'json' : ''}`}>
                                    {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Equity Curve */}
            <div className="charts-grid" style={{ marginTop: '2rem' }}>
                <div className="card chart-card" style={{ gridColumn: '1 / -1' }}>
                    <h3>Equity Curve</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={trades}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="index" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip content={<CustomTooltip />} contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                <Line
                                    type="monotone"
                                    dataKey="cumulativePnl"
                                    stroke="#38bdf8"
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 6 }}
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
