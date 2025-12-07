import React, { createContext, useState, useContext, useEffect } from 'react'
import axios from 'axios'

const StrategyContext = createContext()

export const StrategyProvider = ({ children }) => {
    const [selectedStrategy, setSelectedStrategy] = useState(null)
    const [selectedRun, setSelectedRun] = useState(null)
    const [strategies, setStrategies] = useState([])
    const [runs, setRuns] = useState([])
    const [loading, setLoading] = useState(true)

    // Fetch Strategies on Mount
    useEffect(() => {
        const fetchStrategies = async () => {
            try {
                const res = await axios.get('http://127.0.0.1:8000/api/strategies/')
                setStrategies(res.data)
                if (res.data.length > 0) {
                    setSelectedStrategy(res.data[0].strategy_id)
                }
                setLoading(false)
            } catch (err) {
                console.error("Failed to fetch strategies", err)
                setLoading(false)
            }
        }
        fetchStrategies()
    }, [])

    // Fetch Runs when Strategy Changes
    useEffect(() => {
        if (!selectedStrategy) return

        const fetchRuns = async () => {
            try {
                const res = await axios.get(`http://127.0.0.1:8000/api/strategies/${selectedStrategy}/runs`)
                setRuns(res.data)
                // Select the most recent run by default, or 'All' if we support it
                if (res.data.length > 0) {
                    setSelectedRun(res.data[0].run_id)
                } else {
                    setSelectedRun(null)
                }
            } catch (err) {
                console.error("Failed to fetch runs", err)
            }
        }
        fetchRuns()
    }, [selectedStrategy])

    return (
        <StrategyContext.Provider value={{
            selectedStrategy,
            setSelectedStrategy,
            selectedRun,
            setSelectedRun,
            strategies,
            runs,
            loading
        }}>
            {children}
        </StrategyContext.Provider>
    )
}

export const useStrategy = () => useContext(StrategyContext)
