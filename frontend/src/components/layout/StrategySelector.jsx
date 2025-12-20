import React from 'react'
import { useStrategy } from '../../context/StrategyContext'
import './StrategySelector.css'

const StrategySelector = () => {
    const {
        strategies, selectedStrategy, setSelectedStrategy,
        instances, selectedInstance, setSelectedInstance,
        runs, selectedRun, setSelectedRun
    } = useStrategy()

    return (
        <div className="strategy-selector-container">
            {/* Strategy Select */}
            <div className="selector-group">
                <label>Strategy</label>
                <select
                    value={selectedStrategy || ''}
                    onChange={(e) => setSelectedStrategy(e.target.value)}
                    className="strategy-select"
                >
                    {strategies.length === 0 && <option value="">No Strategies</option>}
                    {strategies.map(s => (
                        <option key={s.strategy_id} value={s.strategy_id}>
                            {s.name}
                        </option>
                    ))}
                </select>
            </div>

            {/* Instance Select */}
            <div className="selector-group">
                <label>Instance</label>
                <select
                    value={selectedInstance || ''}
                    onChange={(e) => setSelectedInstance(e.target.value)}
                    className="strategy-select"
                    disabled={!selectedStrategy || instances.length === 0}
                >
                    {instances.length === 0 && <option value="">No Instances</option>}
                    {instances.map(i => (
                        <option key={i.instance_id} value={i.instance_id}>
                            {i.instance_name || i.instance_id}
                        </option>
                    ))}
                </select>
            </div>

            {/* Run Select */}
            <div className="selector-group">
                <label>Run</label>
                <select
                    value={selectedRun || ''}
                    onChange={(e) => setSelectedRun(e.target.value)}
                    className="run-select"
                    disabled={!selectedInstance || runs.length === 0}
                >
                    {runs.length === 0 && <option value="">No Runs</option>}
                    {runs.map(r => (
                        <option key={r.run_id} value={r.run_id}>
                            {new Date(r.start_utc).toLocaleString()} ({r.status})
                        </option>
                    ))}
                </select>
            </div>
        </div>
    )
}

export default StrategySelector
