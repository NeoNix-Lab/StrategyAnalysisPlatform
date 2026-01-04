import React, { useState, useMemo } from 'react'
import { useStrategyData } from '../hooks/useStrategyData'
import { ArrowDown, ArrowUp, Filter, Search } from 'lucide-react'

const Executions = () => {
    const { executions, loading, error } = useStrategyData()
    const [filterSide, setFilterSide] = useState('ALL')
    const [searchTerm, setSearchTerm] = useState('')

    const filteredExecutions = useMemo(() => {
        return executions.filter(exec => {
            const matchesSide = filterSide === 'ALL' || exec.side === filterSide // Note: Side might not be on Execution directly, usually logic needs Order
            // Actually, Execution doesn't strictly have Side, Order does. 
            // The API/DTO might need to enrich execution with Order Side, or we show what we have.
            // For now, let's assume we filter by ID or convert raw data.

            // If backend doesn't send side in execution list, we can't filter by it easily without joining.
            // Let's filter by ID for now.
            const matchesSearch = exec.execution_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
                exec.order_id.toLowerCase().includes(searchTerm.toLowerCase())
            return matchesSearch
        })
    }, [executions, filterSide, searchTerm])

    if (loading) return <div className="text-center mt-20 text-text-secondary animate-pulse">Loading executions...</div>
    if (error) return <div className="text-center mt-20 text-rose-500">Error loading data: {error.message}</div>

    return (
        <div className="max-w-[1600px] mx-auto animate-fade-in">
            <div className="bg-bg-secondary/50 backdrop-blur-sm border border-slate-700/50 rounded-2xl p-6 shadow-xl">
                <div className="flex justify-between mb-6">
                    <div className="flex items-center gap-4">
                        <h3 className="text-lg font-bold text-text-primary m-0">Execution Log</h3>
                        <span className="bg-slate-700 text-slate-100 px-2 py-0.5 rounded text-xs font-mono">
                            {filteredExecutions.length}
                        </span>
                    </div>
                    <div className="flex gap-4">
                        <div className="bg-slate-800/50 p-2 rounded-lg flex items-center border border-slate-700/50 focus-within:border-sky-500/50 transition-colors">
                            <Search size={16} className="text-slate-400" />
                            <input
                                type="text"
                                placeholder="Search IDs..."
                                value={searchTerm}
                                onChange={e => setSearchTerm(e.target.value)}
                                className="bg-transparent border-none text-slate-100 ml-2 outline-none placeholder:text-slate-600 text-sm w-48"
                            />
                        </div>
                    </div>
                </div>

                <div className="overflow-x-auto custom-scrollbar">
                    <table className="w-full text-sm text-left">
                        <thead className="bg-slate-900/50 text-xs uppercase font-semibold text-text-secondary">
                            <tr>
                                <th className="p-4 border-b border-slate-700/50">Time (UTC)</th>
                                <th className="p-4 border-b border-slate-700/50">Impact</th>
                                <th className="p-4 border-b border-slate-700/50">Price</th>
                                <th className="p-4 border-b border-slate-700/50">Quantity</th>
                                <th className="p-4 border-b border-slate-700/50">Fee</th>
                                <th className="p-4 border-b border-slate-700/50">Liquidity</th>
                                <th className="p-4 border-b border-slate-700/50">IDs</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-slate-800/50">
                            {filteredExecutions.length === 0 ? (
                                <tr>
                                    <td colSpan={7} className="p-12 text-center text-text-secondary">
                                        No executions found for this run.
                                    </td>
                                </tr>
                            ) : (
                                filteredExecutions.map(exec => {
                                    const impactColor = exec.position_impact === 'OPEN' ? 'bg-sky-500/10 text-sky-400' :
                                        exec.position_impact === 'CLOSE' ? 'bg-violet-500/10 text-violet-400' : 'bg-slate-700/50 text-slate-400';

                                    return (
                                        <tr key={exec.execution_id} className="hover:bg-white/5 transition-colors">
                                            <td className="p-4 text-text-secondary whitespace-nowrap">
                                                {new Date(exec.exec_utc).toLocaleTimeString()} <span className="opacity-70 text-xs ml-1">{new Date(exec.exec_utc).toLocaleDateString()}</span>
                                            </td>
                                            <td className="p-4">
                                                <span className={`px-2 py-1 rounded text-[10px] font-bold tracking-wider ${impactColor}`}>
                                                    {exec.position_impact || 'UNKNOWN'}
                                                </span>
                                            </td>
                                            <td className="p-4 font-mono font-semibold text-text-primary">{exec.price.toFixed(2)}</td>
                                            <td className="p-4 font-mono text-text-secondary">{exec.quantity}</td>
                                            <td className={`p-4 font-mono ${exec.fee > 0 ? 'text-rose-400' : 'text-text-secondary'}`}>
                                                {exec.fee ? exec.fee.toFixed(4) : '-'} <span className="text-[10px] opacity-70">{exec.fee_currency}</span>
                                            </td>
                                            <td className="p-4">
                                                <span className={`px-2 py-1 rounded text-xs ${exec.liquidity === 'MAKER' ? 'bg-sky-500/10 text-accent' : 'text-text-secondary'}`}>
                                                    {exec.liquidity || '-'}
                                                </span>
                                            </td>
                                            <td className="p-4 font-mono text-xs text-text-secondary">
                                                <div title={`Exec: ${exec.execution_id}`}>{exec.execution_id.substring(0, 8)}...</div>
                                                <div title={`Order: ${exec.order_id}`} className="opacity-60 mt-0.5">{exec.order_id.substring(0, 8)}...</div>
                                            </td>
                                        </tr>
                                    )
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

export default Executions
