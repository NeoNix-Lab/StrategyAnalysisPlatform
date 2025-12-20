import { useState, useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { useStrategyData } from '../hooks/useStrategyData'
import { ArrowUp, ArrowDown, Filter, Download } from 'lucide-react'

const Trades = () => {
    const navigate = useNavigate()
    const { trades, loading } = useStrategyData()
    const [sortConfig, setSortConfig] = useState({ key: 'exit_time', direction: 'desc' })
    const [filterSide, setFilterSide] = useState('ALL') // ALL, LONG, SHORT
    const [filterResult, setFilterResult] = useState('ALL') // ALL, WIN, LOSS

    // Sorting Logic
    const sortedTrades = useMemo(() => {
        let sortableTrades = [...trades]

        // Filtering
        if (filterSide !== 'ALL') {
            sortableTrades = sortableTrades.filter(t => t.side === filterSide)
        }
        if (filterResult !== 'ALL') {
            sortableTrades = sortableTrades.filter(t =>
                filterResult === 'WIN' ? t.pnl_net > 0 : t.pnl_net <= 0
            )
        }

        // Sorting
        if (sortConfig.key) {
            sortableTrades.sort((a, b) => {
                if (a[sortConfig.key] < b[sortConfig.key]) {
                    return sortConfig.direction === 'asc' ? -1 : 1
                }
                if (a[sortConfig.key] > b[sortConfig.key]) {
                    return sortConfig.direction === 'asc' ? 1 : -1
                }
                return 0
            })
        }
        return sortableTrades
    }, [trades, sortConfig, filterSide, filterResult])

    const requestSort = (key) => {
        let direction = 'asc'
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc'
        }
        setSortConfig({ key, direction })
    }

    const getSortIcon = (name) => {
        if (sortConfig.key !== name) return null
        return sortConfig.direction === 'asc' ? <ArrowUp size={14} /> : <ArrowDown size={14} />
    }

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString()
    }

    if (loading) return <div className="loading">Loading trades...</div>

    return (
        <div className="trades-container">
            <div className="trades-header">
                <h2>Trade History</h2>
                <div className="trades-actions">
                    <div className="filter-group">
                        <Filter size={16} className="filter-icon" />
                        <select value={filterSide} onChange={(e) => setFilterSide(e.target.value)} className="filter-select">
                            <option value="ALL">All Sides</option>
                            <option value="LONG">Long Only</option>
                            <option value="SHORT">Short Only</option>
                        </select>
                        <select value={filterResult} onChange={(e) => setFilterResult(e.target.value)} className="filter-select">
                            <option value="ALL">All Results</option>
                            <option value="WIN">Winners</option>
                            <option value="LOSS">Losers</option>
                        </select>
                    </div>
                    <button className="export-btn">
                        <Download size={16} /> Export CSV
                    </button>
                </div>
            </div>

            <div className="table-container">
                <table className="trades-table">
                    <thead>
                        <tr>
                            <th onClick={() => requestSort('index')}># {getSortIcon('index')}</th>
                            <th onClick={() => requestSort('symbol')}>Symbol {getSortIcon('symbol')}</th>
                            <th onClick={() => requestSort('side')}>Side {getSortIcon('side')}</th>
                            <th onClick={() => requestSort('entry_time')}>Entry Time {getSortIcon('entry_time')}</th>
                            <th onClick={() => requestSort('exit_time')}>Exit Time {getSortIcon('exit_time')}</th>
                            <th onClick={() => requestSort('duration_seconds')}>Duration {getSortIcon('duration_seconds')}</th>
                            <th onClick={() => requestSort('pnl_net')} className="text-right">PnL Net {getSortIcon('pnl_net')}</th>
                            <th onClick={() => requestSort('mae')} className="text-right">MAE {getSortIcon('mae')}</th>
                            <th onClick={() => requestSort('mfe')} className="text-right">MFE {getSortIcon('mfe')}</th>
                            <th className="text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sortedTrades.map((trade) => (
                            <tr
                                key={trade.trade_id}
                                className="trade-row cursor-pointer hover:bg-slate-800 transition-colors"
                                onClick={() => navigate(`/trades/${trade.trade_id}`)}
                            >
                                <td>{trade.index}</td>
                                <td className="font-mono">{trade.symbol}</td>
                                <td>
                                    <span className={`badge ${trade.side === 'LONG' ? 'badge-long' : 'badge-short'}`}>
                                        {trade.side}
                                    </span>
                                </td>
                                <td className="text-sm text-secondary">{formatDate(trade.entry_time)}</td>
                                <td className="text-sm text-secondary">{formatDate(trade.exit_time)}</td>
                                <td className="text-sm">{(trade.duration_seconds / 60).toFixed(1)}m</td>
                                <td className={`text-right font-bold ${trade.pnl_net > 0 ? 'text-success' : 'text-danger'}`}>
                                    {trade.pnl_net.toFixed(2)} €
                                </td>
                                <td className="text-right text-secondary">{trade.mae.toFixed(2)}</td>
                                <td className="text-right text-secondary">{trade.mfe.toFixed(2)}</td>
                                <td className="text-right" onClick={(e) => e.stopPropagation()}>
                                    <button
                                        className="action-btn"
                                        style={{ background: 'transparent', border: '1px solid #334155', color: '#94a3b8', borderRadius: '4px', cursor: 'pointer', padding: '2px 8px' }}
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            navigate(`/trades/${trade.trade_id}/replay`);
                                        }}
                                    >
                                        Replay
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>

            <div className="table-footer">
                Showing {sortedTrades.length} trades
            </div>
        </div>
    )
}

export default Trades
