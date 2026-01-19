import { useState, useEffect } from 'react'
import api from '../api/axios'
import { useStrategy } from '../context/StrategyContext'

export const useStrategyData = () => {
    const { selectedRun } = useStrategy()
    const [stats, setStats] = useState(null)
    const [trades, setTrades] = useState([])
    const [executions, setExecutions] = useState([])
    const [regimePerformance, setRegimePerformance] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    const fetchData = async () => {
        if (!selectedRun) {
            setLoading(false)
            setTrades([])
            setStats(null)
            return
        }

        try {
            setLoading(true)
            setRegimePerformance(null)

            // 1. Fetch Run Stats (Metrics)
            const runRes = await api.get(`/runs/${selectedRun}`)
            const runData = runRes.data

            if (runData.metrics_json) {
                setStats(runData.metrics_json)
            } else {
                setStats({
                    net_profit: 0,
                    win_rate: 0,
                    profit_factor: 0,
                    max_drawdown: 0,
                    sharpe_ratio: 0,
                    sortino_ratio: 0,
                    calmar_ratio: 0,
                    avg_mae: 0,
                    efficiency_ratio: 0,
                    max_consecutive_wins: 0,
                    max_consecutive_losses: 0,
                    total_fees: 0,
                    total_volume: 0,
                    stability_r2: 0,
                    pnl_skew: 0,
                    pnl_kurtosis: 0
                })
            }

            // 2. Fetch Executions
            const execRes = await api.get(`/executions/run/${selectedRun}`)
            setExecutions(execRes.data)

            // 3. Fetch Reconstructed Trades
            try {
                const tradesRes = await api.get(`/runs/${selectedRun}/trades`)
                const processedTrades = tradesRes.data.map((t, index) => ({
                    ...t,
                    index: index + 1,
                    mae: t.mae || 0,
                    mfe: t.mfe || 0
                }))
                setTrades(processedTrades)
            } catch (tradeErr) {
                console.warn("Failed to fetch trades or no trades found", tradeErr)
                setTrades([])
            }

            try {
                const regimeRes = await api.get(`/regime/${selectedRun}`)
                setRegimePerformance(regimeRes.data.regime_performance)
            } catch (regimeErr) {
                console.warn("Failed to fetch regime performance", regimeErr)
                setRegimePerformance(null)
            }

            setLoading(false)
        } catch (err) {
            console.error("Error fetching data:", err)
            setError(err)
            setLoading(false)
        }
    }

    useEffect(() => {
        fetchData()
    }, [selectedRun])

    return { stats, trades, executions, regimePerformance, loading, error, refresh: fetchData }
}
