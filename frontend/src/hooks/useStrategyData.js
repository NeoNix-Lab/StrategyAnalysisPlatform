import { useState, useEffect } from 'react'
import axios from 'axios'
import { useStrategy } from '../context/StrategyContext'

export const useStrategyData = () => {
    const { selectedStrategy, selectedRun } = useStrategy()
    const [stats, setStats] = useState(null)
    const [trades, setTrades] = useState([])
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (!selectedStrategy) return

        const fetchData = async () => {
            try {
                setLoading(true)

                // Build query params
                let params = `strategy_id=${selectedStrategy}`
                if (selectedRun) {
                    params += `&run_id=${selectedRun}`
                }

                const [statsRes, tradesRes] = await Promise.all([
                    axios.get(`http://127.0.0.1:8000/api/trades/stats?${params}`),
                    axios.get(`http://127.0.0.1:8000/api/trades/?${params}&limit=1000`)
                ])

                setStats(statsRes.data)

                let cumulativePnl = 0
                const processedTrades = tradesRes.data.map((t, index) => {
                    cumulativePnl += t.pnl_net
                    return {
                        ...t,
                        index: index + 1,
                        cumulativePnl: cumulativePnl,
                        mae: t.mae || 0,
                        mfe: t.mfe || 0,
                        pnlColor: t.pnl_net > 0 ? '#4ade80' : '#f87171'
                    }
                })

                setTrades(processedTrades)
                setLoading(false)
            } catch (err) {
                console.error("Error fetching data:", err)
                setError(err)
                setLoading(false)
            }
        }

        fetchData()
    }, [selectedStrategy, selectedRun])

    return { stats, trades, loading, error }
}
