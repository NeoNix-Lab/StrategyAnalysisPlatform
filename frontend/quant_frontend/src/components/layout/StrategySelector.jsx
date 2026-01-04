import React from 'react'
import { useStrategy } from '../../context/StrategyContext'

const StrategySelector = () => {
    const {
        strategies, selectedStrategy, setSelectedStrategy,
        instances, selectedInstance, setSelectedInstance,
        runs, selectedRun, setSelectedRun
    } = useStrategy()

    const selectClass = `
        bg-slate-800/50 backdrop-blur-sm border border-slate-700/50 text-slate-50
        py-1.5 px-3 rounded-lg text-sm min-w-[140px] outline-none cursor-pointer transition-all duration-200
        hover:border-accent/50 hover:bg-slate-800/80
        focus:border-accent focus:ring-1 focus:ring-accent/50 focus:bg-slate-900
        disabled:opacity-50 disabled:cursor-not-allowed
    `

    const labelClass = "text-[10px] uppercase text-slate-400 font-bold mb-1 tracking-wide"

    return (
        <div className="flex items-center gap-4">
            {/* Strategy Select */}
            <div className="flex flex-col">
                <label className={labelClass}>Strategy</label>
                <select
                    value={selectedStrategy || ''}
                    onChange={(e) => setSelectedStrategy(e.target.value)}
                    className={selectClass}
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
            <div className="flex flex-col">
                <label className={labelClass}>Instance</label>
                <select
                    value={selectedInstance || ''}
                    onChange={(e) => setSelectedInstance(e.target.value)}
                    className={selectClass}
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
            <div className="flex flex-col">
                <label className={labelClass}>Run</label>
                <select
                    value={selectedRun || ''}
                    onChange={(e) => setSelectedRun(e.target.value)}
                    className={selectClass}
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

