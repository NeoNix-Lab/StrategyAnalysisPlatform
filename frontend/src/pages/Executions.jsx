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
                                <th>Execution ID</th>
                                <th>Order ID</th>
                                <th>Price</th>
                                <th>Quantity</th>
                                <th>Fee</th>
                            </tr>
                        </thead>
                        <tbody>
                            {filteredExecutions.length === 0 ? (
                                <tr>
                                    <td colSpan={6} style={{ textAlign: 'center', padding: '2rem', color: '#64748b' }}>
                                        No executions found for this run.
                                    </td>
                                </tr>
                            ) : (
                                filteredExecutions.map(exec => (
                                    <tr key={exec.execution_id}>
                                        <td>{new Date(exec.exec_utc).toLocaleString()}</td>
                                        <td className="mono">{exec.execution_id}</td>
                                        <td className="mono">{exec.order_id}</td>
                                        <td className="num">{exec.price}</td>
                                        <td className="num">{exec.quantity}</td>
                                        <td className="num">{exec.fee} {exec.fee_currency}</td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    )
}

export default Executions
