import { useState, useEffect, useMemo } from 'react'
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, Cell, LineChart, Line, ReferenceLine, Legend } from 'recharts'
import { useStrategyData } from '../hooks/useStrategyData'
import { CandleChart } from '../components/CandleChart'
import { X, Info } from 'lucide-react'
import api from '../api/axios'

const Efficiency = () => {
    const { trades, loading } = useStrategyData()

    // State for Trade Inspector
    const [selectedTrade, setSelectedTrade] = useState(null)
    const [inspectorData, setInspectorData] = useState(null)
    const [inspectorLoading, setInspectorLoading] = useState(false)

    // --- Advanced Metrics Calculation ---
    const enrichedTrades = useMemo(() => {
        return trades.map(t => {
            // Calcolo Exit Efficiency usando Price Delta per evitare problemi di Multiplier
            // Captured Delta = (Exit - Entry) per Buy, (Entry - Exit) per Sell
            const isBuy = t.side === 'BUY' || t.side === 'LONG' // Handle potential variations
            const capturedDelta = isBuy ? (t.exit_price - t.entry_price) : (t.entry_price - t.exit_price)

            // Potential Delta (MFE) è sempre positivo (distanza massima favorevole)
            const potentialDelta = t.mfe || 0

            // Potential Profit (Gross stimato senza multiplier, utile solo per pesature interne)
            const potentialProfit = potentialDelta * t.quantity

            let exitEff = 0
            if (potentialDelta > 0) {
                // Efficienza = Quanto del movimento potenziale abbiamo catturato?
                // Può essere negativo se il trade è in perdita.
                exitEff = (capturedDelta / potentialDelta) * 100
            }

            // Cap a 110% per outlier
            // Se exitEff è molto negativo (es. -200%), lo lasciamo o lo clippiamo?
            // Per distribuzione bucket (0-100), i negativi vanno esclusi o messi in bucket 0.
            // Qui lasciamo il valore raw, la logica di visualizzazione filtrerà.
            if (exitEff > 110) exitEff = 110

            return {
                ...t,
                exitEfficiency: exitEff,
                potentialProfit: potentialProfit,
                maeValue: t.mae * t.quantity
            }
        })
    }, [trades])

    // Histogram Data for Exit Efficiency
    const efficiencyDistribution = useMemo(() => {
        const buckets = Array(11).fill(0).map((_, i) => ({ range: `${i * 10}-${(i + 1) * 10}%`, count: 0, min: i * 10, max: (i + 1) * 10 }))
        enrichedTrades.forEach(t => {
            if (t.pnl_net > 0) { // Solo per trade vincenti
                const bucketIndex = Math.min(Math.floor(t.exitEfficiency / 10), 10)
                buckets[bucketIndex].count++
            }
        })
        return buckets
    }, [enrichedTrades])

    // Fetch bars when a trade is selected
    useEffect(() => {
        if (!selectedTrade) return;

        const fetchBars = async () => {
            setInspectorLoading(true)
            try {
                const entryTime = new Date(selectedTrade.entry_time)
                const exitTime = new Date(selectedTrade.exit_time)
                const startTime = new Date(entryTime.getTime() - 20 * 60000).toISOString()
                const endTime = new Date(exitTime.getTime() + 20 * 60000).toISOString()

                const res = await api.get('/bars/', {
                    params: {
                        symbol: selectedTrade.symbol,
                        start_time: startTime,
                        end_time: endTime
                    }
                })
                setInspectorData(res.data)
            } catch (error) {
                console.error("Error fetching bars:", error)
            } finally {
                setInspectorLoading(false)
            }
        }

        fetchBars()
    }, [selectedTrade])

    const handleTradeClick = (trade) => {
        if (trade && trade.payload) {
            setSelectedTrade(trade.payload)
        }
    }

    if (loading) return <div className="loading">Loading efficiency metrics...</div>

    return (
        <div className="efficiency-container">
            <div className="charts-grid">
                {/* MAE vs MFE Scatter */}
                <div className="card chart-card">
                    <div className="card-header-row">
                        <h3>MAE vs MFE (Risk vs Potential)</h3>
                        <div className="tooltip-icon" title="Analizza quanto rischio (MAE) hai corso per ottenere il potenziale (MFE). I trade ideali sono in alto a sinistra (Basso MAE, Alto MFE).">
                            <Info size={16} color="#94a3b8" />
                        </div>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <ScatterChart>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis type="number" dataKey="mae" name="MAE" unit="€" stroke="#94a3b8" label={{ value: 'MAE (Risk)', position: 'bottom', fill: '#94a3b8' }} />
                                <YAxis type="number" dataKey="mfe" name="MFE" unit="€" stroke="#94a3b8" label={{ value: 'MFE (Potential)', angle: -90, position: 'left', fill: '#94a3b8' }} />
                                <ZAxis type="number" dataKey="pnl_net" range={[50, 400]} name="PnL" />
                                <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                <Scatter
                                    name="Trades"
                                    data={enrichedTrades}
                                    fill="#8884d8"
                                    onClick={handleTradeClick}
                                    style={{ cursor: 'pointer' }}
                                >
                                    {enrichedTrades.map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.pnlColor} />
                                    ))}
                                </Scatter>
                            </ScatterChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Exit Efficiency Histogram */}
                <div className="card chart-card">
                    <div className="card-header-row">
                        <h3>Exit Efficiency Distribution (Winners)</h3>
                        <div className="tooltip-icon" title="% del movimento massimo (MFE) catturato. Valori alti indicano uscite ottimali.">
                            <Info size={16} color="#94a3b8" />
                        </div>
                    </div>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <BarChart data={efficiencyDistribution}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="range" stroke="#94a3b8" />
                                <YAxis stroke="#94a3b8" />
                                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                <Bar dataKey="count" name="Trades" fill="#38bdf8" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                </div>

                {/* Efficiency Timeline */}
                <div className="card chart-card" style={{ gridColumn: '1 / -1' }}>
                    <h3>Exit Efficiency Timeline</h3>
                    <div className="chart-container">
                        <ResponsiveContainer width="100%" height="100%">
                            <LineChart data={enrichedTrades.filter(t => t.pnl_net > 0)}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                                <XAxis dataKey="index" stroke="#94a3b8" />
                                <YAxis unit="%" stroke="#94a3b8" domain={[0, 100]} />
                                <Tooltip contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }} />
                                <Legend />
                                <Line type="monotone" dataKey="exitEfficiency" name="Exit Efficiency %" stroke="#4ade80" dot={false} strokeWidth={2} />
                                <ReferenceLine y={50} stroke="#94a3b8" strokeDasharray="3 3" label="50%" />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                </div>
            </div>

            {/* Trade Inspector Modal (Invariato) */}
            {selectedTrade && (
                <div className="inspector-overlay">
                    <div className="inspector-modal">
                        <div className="inspector-header">
                            <h2>Trade Inspector #{selectedTrade.index}</h2>
                            <button className="close-btn" onClick={() => setSelectedTrade(null)}>
                                <X size={24} />
                            </button>
                        </div>

                        <div className="inspector-content">
                            <div className="inspector-stats">
                                <div className="stat-item">
                                    <span className="label">PnL</span>
                                    <span className={`value ${selectedTrade.pnl_net > 0 ? 'positive' : 'negative'}`}>
                                        {selectedTrade.pnl_net.toFixed(2)} €
                                    </span>
                                </div>
                                <div className="stat-item">
                                    <span className="label">Exit Eff.</span>
                                    <span className="value">{selectedTrade.exitEfficiency?.toFixed(1)}%</span>
                                </div>
                                <div className="stat-item">
                                    <span className="label">MAE</span>
                                    <span className="value">{selectedTrade.mae.toFixed(2)}</span>
                                </div>
                                <div className="stat-item">
                                    <span className="label">MFE</span>
                                    <span className="value">{selectedTrade.mfe.toFixed(2)}</span>
                                </div>
                            </div>

                            <div className="inspector-chart">
                                {inspectorLoading ? (
                                    <div className="loading-small">Loading chart data...</div>
                                ) : inspectorData ? (
                                    <CandleChart data={inspectorData} trade={selectedTrade} width={800} height={400} />
                                ) : (
                                    <div className="error">No data available</div>
                                )}
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}

export default Efficiency
