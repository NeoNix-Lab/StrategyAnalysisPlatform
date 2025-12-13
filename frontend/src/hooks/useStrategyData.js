import { useState, useEffect } from 'react'
import axios from 'axios'
import { useStrategy } from '../context/StrategyContext'

export const useStrategyData = () => {
    const { selectedRun } = useStrategy()
    const [stats, setStats] = useState(null)
    const [trades, setTrades] = useState([]) // Now Executions
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const API_URL = 'http://127.0.0.1:8000/api'

    useEffect(() => {
        if (!selectedRun) {
            setLoading(false)
            setTrades([])
            setStats(null)
            return
        }

        const fetchData = async () => {
            try {
                setLoading(true)

                // 1. Fetch Run Stats (Metrics)
                const runRes = await axios.get(`${API_URL}/runs/${selectedRun}`)
                const runData = runRes.data

                if (runData.metrics_json) {
                    setStats(runData.metrics_json)
                } else {
                    setStats({
                        net_profit: 0,
                        win_rate: 0,
                        profit_factor: 0,
                        max_drawdown: 0
                    })
                }

                // 2. Fetch Executions instead of Trades
                const execRes = await axios.get(`${API_URL}/executions/run/${selectedRun}`)

                // Map executions to a format that won't break the UI
                const processed = execRes.data.map((e, index) => ({
                    ...e,
                    id: e.execution_id, // UI uses id
                    index: index + 1,
                    cumulativePnl: 0, // Placeholder
                    pnl_net: 0,
                    pnlColor: '#aaaaaa'
                }))

                setTrades(processed)
                setLoading(false)
            } catch (err) {
                console.error("Error fetching data:", err)
                setError(err)
                setLoading(false)
            }
        }

        fetchData()
    }, [selectedRun])

    return { stats, trades, loading, error }
}
