import { useStrategyData } from '../hooks/useStrategyData'
import { useStrategy } from '../context/StrategyContext'
import { Sliders, Activity, DollarSign, TrendingUp, AlertTriangle } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'
import './Dashboard.css'

const Dashboard = () => {
    const { trades: executions, loading } = useStrategyData()
    const { runs, selectedRun, instances, selectedInstance } = useStrategy()

    const currentRun = runs.find(r => r.run_id === selectedRun)
    const currentInstance = instances.find(i => i.instance_id === selectedInstance)

    // Calculate simple metrics locally since backend analytics is disabled
    const totalExecutions = executions.length
    const totalVolume = executions.reduce((acc, curr) => acc + (curr.price * curr.quantity), 0)
    const fees = executions.reduce((acc, curr) => acc + (curr.fee || 0), 0)

    // Mock Equity Curve (Cumulative Volume/Cost as proxy for activity, strictly NOT PnL)
    // Real PnL requires Trade Reconstruction (Entry vs Exit).
    // Use a placeholder chart or just execution count over time.
    const chartData = executions.map((e, i) => ({
        index: i,
        price: e.price,
        time: new Date(e.exec_utc).toLocaleTimeString()
    }))

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
                    <h3>Total Executions</h3>
                    <div className="metric-value">{totalExecutions}</div>
                </div>
                <div className="card">
                    <div className="card-icon"><TrendingUp size={24} color="#4ade80" /></div>
                    <h3>Total Volume</h3>
                    <div className="metric-value">{totalVolume.toFixed(2)} <span style={{ fontSize: '0.6em' }}>USD</span></div>
                </div>
                <div className="card">
                    <div className="card-icon"><DollarSign size={24} color="#f87171" /></div>
                    <h3>Total Fees</h3>
                    <div className="metric-value negative">{fees.toFixed(4)}</div>
                </div>
                <div className="card">
                    <div className="card-icon"><AlertTriangle size={24} color="#facc15" /></div>
                    <h3>PnL Status</h3>
                    <div className="metric-value" style={{ fontSize: '1.2rem', color: '#facc15' }}>Pending Analytics</div>
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

            {/* Execution Activity Chart */}
            <div className="charts-grid" style={{ marginTop: '2rem' }}>
                <div className="card chart-card" style={{ gridColumn: '1 / -1' }}>
                    <h3>Execution Prices (Raw)</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={chartData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="index" stroke="#94a3b8" />
                                <YAxis domain={['auto', 'auto']} stroke="#94a3b8" />
                                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                <Line
                                    type="monotone"
                                    dataKey="price"
                                    stroke="#38bdf8"
                                    strokeWidth={2}
                                    dot={true}
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
