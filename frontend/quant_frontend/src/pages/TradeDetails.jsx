import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { ArrowLeft, TrendingUp, TrendingDown, Clock, DollarSign } from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ReferenceLine, ReferenceDot } from 'recharts'

const TradeDetails = () => {
    const { tradeId } = useParams()
    const navigate = useNavigate()
    const [trade, setTrade] = useState(null)
    const [bars, setBars] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        const fetchTradeDetails = async () => {
            try {
                setLoading(true)
                // 1. Get Trade Details
                const tradeRes = await axios.get(`http://127.0.0.1:8000/api/trades/${tradeId}`)
                const tradeData = tradeRes.data
                setTrade(tradeData)

                // 2. Get Bars for the trade duration (with buffer)
                // Add 10% buffer before and after
                const entryTime = new Date(tradeData.entry_time)
                const exitTime = new Date(tradeData.exit_time)
                const duration = exitTime - entryTime
                const buffer = Math.max(duration * 0.2, 60000 * 5) // Min 5 mins buffer

                const startTime = new Date(entryTime.getTime() - buffer).toISOString()
                const endTime = new Date(exitTime.getTime() + buffer).toISOString()

                const barsRes = await axios.get(`http://127.0.0.1:8000/api/bars/`, {
                    params: {
                        symbol: tradeData.symbol,
                        start_time: startTime,
                        end_time: endTime,
                        limit: 5000
                    }
                })

                // Format bars for chart
                const formattedBars = barsRes.data.map(b => ({
                    ...b,
                    time: new Date(b.timestamp).toLocaleTimeString(),
                    fullTime: b.timestamp
                }))
                setBars(formattedBars)

            } catch (err) {
                console.error("Error fetching trade details:", err)
                setError("Failed to load trade data.")
            } finally {
                setLoading(false)
            }
        }

        if (tradeId) {
            fetchTradeDetails()
        }
    }, [tradeId])

    if (loading) return <div className="p-8 text-center">Loading trade details...</div>
    if (error) return <div className="p-8 text-center text-red-500">{error}</div>
    if (!trade) return <div className="p-8 text-center">Trade not found</div>

    const isWin = trade.pnl_net > 0
    const durationMinutes = (new Date(trade.exit_time) - new Date(trade.entry_time)) / 60000

    return (
        <div className="p-6 max-w-7xl mx-auto">
            <button
                onClick={() => navigate(-1)}
                className="flex items-center gap-2 text-gray-400 hover:text-white mb-6 transition-colors"
            >
                <ArrowLeft size={20} /> Back to Trades
            </button>

            {/* Header Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <div className="text-slate-400 text-sm mb-1">Net PnL</div>
                    <div className={`text-2xl font-bold flex items-center gap-2 ${isWin ? 'text-green-400' : 'text-red-400'}`}>
                        <DollarSign size={24} />
                        {trade.pnl_net.toFixed(2)}
                    </div>
                </div>

                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <div className="text-slate-400 text-sm mb-1">Side</div>
                    <div className={`text-2xl font-bold flex items-center gap-2 ${trade.side === 'LONG' ? 'text-blue-400' : 'text-orange-400'}`}>
                        {trade.side === 'LONG' ? <TrendingUp size={24} /> : <TrendingDown size={24} />}
                        {trade.side}
                    </div>
                </div>

                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <div className="text-slate-400 text-sm mb-1">Duration</div>
                    <div className="text-2xl font-bold flex items-center gap-2 text-slate-200">
                        <Clock size={24} />
                        {durationMinutes.toFixed(1)} min
                    </div>
                </div>

                <div className="bg-slate-800 p-6 rounded-xl border border-slate-700">
                    <div className="text-slate-400 text-sm mb-1">Symbol</div>
                    <div className="text-2xl font-bold text-slate-200">
                        {trade.symbol}
                    </div>
                </div>
            </div>

            {/* Chart */}
            <div className="bg-slate-800 p-6 rounded-xl border border-slate-700 h-[500px] mb-8">
                <h3 className="text-xl font-semibold mb-4 text-slate-200">Price Action Execution</h3>
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={bars}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                        <XAxis
                            dataKey="time"
                            stroke="#94a3b8"
                            minTickGap={50}
                        />
                        <YAxis
                            domain={['auto', 'auto']}
                            stroke="#94a3b8"
                            tickFormatter={(val) => val.toFixed(2)}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155' }}
                            labelStyle={{ color: '#94a3b8' }}
                        />
                        <Line
                            type="monotone"
                            dataKey="close"
                            stroke="#64748b"
                            strokeWidth={2}
                            dot={false}
                        />

                        {/* Entry Marker */}
                        <ReferenceDot
                            x={new Date(trade.entry_time).toLocaleTimeString()}
                            y={trade.entry_price}
                            r={6}
                            fill="#3b82f6"
                            stroke="#fff"
                        />

                        {/* Exit Marker */}
                        <ReferenceDot
                            x={new Date(trade.exit_time).toLocaleTimeString()}
                            y={trade.exit_price}
                            r={6}
                            fill={isWin ? "#22c55e" : "#ef4444"}
                            stroke="#fff"
                        />

                        {/* Entry Line */}
                        <ReferenceLine
                            y={trade.entry_price}
                            stroke="#3b82f6"
                            strokeDasharray="3 3"
                            label={{ position: 'right', value: 'Entry', fill: '#3b82f6' }}
                        />
                    </LineChart>
                </ResponsiveContainer>
            </div>

            {/* Details Table */}
            <div className="bg-slate-800 rounded-xl border border-slate-700 overflow-hidden">
                <div className="p-6 border-b border-slate-700">
                    <h3 className="text-xl font-semibold text-slate-200">Execution Details</h3>
                </div>
                <div className="grid grid-cols-2 gap-6 p-6">
                    <div>
                        <div className="flex justify-between py-3 border-b border-slate-700">
                            <span className="text-slate-400">Entry Time</span>
                            <span className="text-slate-200">{new Date(trade.entry_time).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between py-3 border-b border-slate-700">
                            <span className="text-slate-400">Entry Price</span>
                            <span className="text-slate-200">{trade.entry_price}</span>
                        </div>
                        <div className="flex justify-between py-3 border-b border-slate-700">
                            <span className="text-slate-400">Quantity</span>
                            <span className="text-slate-200">{trade.quantity}</span>
                        </div>
                    </div>
                    <div>
                        <div className="flex justify-between py-3 border-b border-slate-700">
                            <span className="text-slate-400">Exit Time</span>
                            <span className="text-slate-200">{new Date(trade.exit_time).toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between py-3 border-b border-slate-700">
                            <span className="text-slate-400">Exit Price</span>
                            <span className="text-slate-200">{trade.exit_price}</span>
                        </div>
                        <div className="flex justify-between py-3 border-b border-slate-700">
                            <span className="text-slate-400">MAE / MFE</span>
                            <span className="text-slate-200">{trade.mae?.toFixed(2)} / {trade.mfe?.toFixed(2)}</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

export default TradeDetails
