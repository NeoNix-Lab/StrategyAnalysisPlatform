import React, { useState, useMemo } from 'react'
import { useStrategyData } from '../hooks/useStrategyData'
import { ArrowDown, ArrowUp, Filter, Search } from 'lucide-react'
import './Dashboard.css' // Reuse dashboard styles for cards

const Executions = () => {
    const { trades: executions, loading, error } = useStrategyData()
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

    if (loading) return <div className="loading">Loading executions...</div>
    if (error) return <div className="error">Error loading data: {error.message}</div>

    return (
        <div className="dashboard-container">
            <div className="card">
                <div className="card-header" style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
                    <h3>Execution Log</h3>
                    <div style={{ display: 'flex', gap: '1rem' }}>
                        <div className="search-box" style={{ background: '#1e293b', padding: '0.5rem', borderRadius: '6px', display: 'flex', alignItems: 'center' }}>
                            <Search size={16} color="#94a3b8" />
                            <input
                                type="text"
                                placeholder="Search IDs..."
                                value={searchTerm}
                                onChange={e => setSearchTerm(e.target.value)}
                                style={{ background: 'transparent', border: 'none', color: 'white', marginLeft: '0.5rem', outline: 'none' }}
                            />
                        </div>
                    </div>
                </div>

                <div className="table-container">
                    <table className="data-table">
                        <thead>
                            <tr>
                                <th>Time (UTC)</th>
                                <th>Impact</th>
                                <th>Price</th>
                                <th>Quantity</th>
                                <th>Fee</th>
                                <th>Liquidity</th>
                                <th>IDs</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredExecutions.length === 0 ? (
                                <tr>
                                    <td colSpan={7} style={{ textAlign: 'center', padding: '3rem', color: 'var(--text-secondary)' }}>
                                        No executions found for this run.
                                    </td>
                                </tr>
                            ) : (
                                filteredExecutions.map(exec => {
                                    const impactClass = `badge-${exec.position_impact?.toLowerCase() || 'unknown'}`
                                    return (
                                        <tr key={exec.execution_id} className="trade-row">
                                            <td style={{ whiteSpace: 'nowrap', color: 'var(--text-secondary)' }}>
                                                {new Date(exec.exec_utc).toLocaleTimeString()} <span style={{ fontSize: '0.8em', opacity: 0.7 }}>{new Date(exec.exec_utc).toLocaleDateString()}</span>
                                            </td>
                                            <td>
                                                <span className={`badge ${impactClass}`}>
                                                    {exec.position_impact || 'UNKNOWN'}
                                                </span>
                                            </td>
                                            <td className="num font-mono" style={{ fontWeight: 600 }}>{exec.price.toFixed(2)}</td>
                                            <td className="num font-mono">{exec.quantity}</td>
                                            <td className="num" style={{ color: exec.fee > 0 ? 'var(--danger)' : 'var(--text-secondary)' }}>
                                                {exec.fee ? exec.fee.toFixed(4) : '-'} <span style={{ fontSize: '0.7em' }}>{exec.fee_currency}</span>
                                            </td>
                                            <td>
                                                <span style={{
                                                    fontSize: '0.75rem',
                                                    padding: '0.2rem 0.5rem',
                                                    borderRadius: '4px',
                                                    background: exec.liquidity === 'MAKER' ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
                                                    color: exec.liquidity === 'MAKER' ? 'var(--accent)' : 'var(--text-secondary)'
                                                }}>
                                                    {exec.liquidity || '-'}
                                                </span>
                                            </td>
                                            <td className="mono" style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                                                <div title={`Exec: ${exec.execution_id}`}>{exec.execution_id.substring(0, 8)}...</div>
                                                <div title={`Order: ${exec.order_id}`} style={{ opacity: 0.7 }}>{exec.order_id.substring(0, 8)}...</div>
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
