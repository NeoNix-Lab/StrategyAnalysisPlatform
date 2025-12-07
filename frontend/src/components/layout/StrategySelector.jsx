import React from 'react'
import { useStrategy } from '../../context/StrategyContext'
import './StrategySelector.css'

const StrategySelector = () => {
    const {
        strategies,
        selectedStrategy,
        setSelectedStrategy,
        runs,
        selectedRun,
        setSelectedRun
    } = useStrategy()

    return (
        <div className="strategy-selector-container">
            <select
                value={selectedStrategy || ''}
                onChange={(e) => setSelectedStrategy(e.target.value)}
                className="strategy-select"
            >
                {strategies.map(s => (
                    <option key={s.strategy_id} value={s.strategy_id}>
                        {s.name}
                    </option>
                ))}
            </select>

            {runs.length > 0 && (
                <select
                    value={selectedRun || ''}
                    onChange={(e) => setSelectedRun(e.target.value)}
                    className="run-select"
                >
                    {runs.map(r => (
                        <option key={r.run_id} value={r.run_id}>
                            {new Date(r.start_time).toLocaleString()} ({r.status})
                        </option>
                    ))}
                </select>
            )}
        </div>
    )
}

export default StrategySelector
