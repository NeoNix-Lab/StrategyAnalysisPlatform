import React, { createContext, useState, useContext, useEffect } from 'react'
import axios from 'axios'

const StrategyContext = createContext()

export const StrategyProvider = ({ children }) => {
    const [selectedStrategy, setSelectedStrategy] = useState(null)
    const [selectedInstance, setSelectedInstance] = useState(null)
    const [selectedRun, setSelectedRun] = useState(null)

    const [strategies, setStrategies] = useState([])
    const [instances, setInstances] = useState([])
    const [runs, setRuns] = useState([])

    const [loading, setLoading] = useState(true)

    const API_URL = 'http://127.0.0.1:8000/api'

    // Fetch Strategies
    useEffect(() => {
        const fetchStrategies = async () => {
            try {
                const res = await axios.get(`${API_URL}/strategies/`)
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

    // Fetch Instances
    useEffect(() => {
        if (!selectedStrategy) {
            setInstances([])
            setSelectedInstance(null)
            return
        }
        const fetchInstances = async () => {
            try {
                const res = await axios.get(`${API_URL}/strategies/${selectedStrategy}/instances`)
                setInstances(res.data)
                if (res.data.length > 0) {
                    setSelectedInstance(res.data[0].instance_id)
                } else {
                    setSelectedInstance(null)
                }
            } catch (err) {
                console.error("Failed to fetch instances", err)
                setInstances([])
            }
        }
        fetchInstances()
    }, [selectedStrategy])

    // Track selectedRun without triggering strict dependency loops
    const selectedRunRef = React.useRef(selectedRun)
    useEffect(() => {
        selectedRunRef.current = selectedRun
    }, [selectedRun])

    // Fetch Runs
    useEffect(() => {
        if (!selectedInstance) {
            setRuns([])
            setSelectedRun(null)
            return
        }

        const fetchRuns = async () => {
            try {
                const res = await axios.get(`${API_URL}/runs/instance/${selectedInstance}`)
                // Sort descending by start_utc
                const sorted = res.data.sort((a, b) => new Date(b.start_utc) - new Date(a.start_utc))
                setRuns(sorted)

                if (sorted.length > 0) {
                    // [FIX] Only auto-select default if current selection is invalid for this instance
                    const currentIsValid = sorted.some(r => r.run_id === selectedRunRef.current)
                    if (!currentIsValid) {
                        setSelectedRun(sorted[0].run_id)
                    }
                } else {
                    setSelectedRun(null)
                }
            } catch (err) {
                console.error("Failed to fetch runs", err)
            }
        }
        fetchRuns()
    }, [selectedInstance])

    return (
        <StrategyContext.Provider value={{
            selectedStrategy, setSelectedStrategy,
            selectedInstance, setSelectedInstance,
            selectedRun, setSelectedRun,
            strategies,
            instances,
            runs,
            loading
        }}>
            {children}
        </StrategyContext.Provider>
    )
}

export const useStrategy = () => useContext(StrategyContext)
