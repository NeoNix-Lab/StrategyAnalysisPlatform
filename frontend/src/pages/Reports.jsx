import { useState } from 'react'
import { useStrategyData } from '../hooks/useStrategyData'
import { Download, FileText, Table, BarChart3 } from 'lucide-react'

const Reports = () => {
    const { trades, stats, loading } = useStrategyData()
    const [exportFormat, setExportFormat] = useState('csv')

    const exportToCSV = () => {
        if (!trades.length) return

        // Prepare CSV headers
        const headers = [
            'Trade ID', 'Symbol', 'Side', 'Entry Time', 'Exit Time',
            'Entry Price', 'Exit Price', 'Quantity', 'PnL Net', 'Commission',
            'MAE', 'MFE', 'Duration (s)', 'Regime Trend', 'Regime Volatility', 'Setup Tag'
        ]

        // Prepare CSV rows
        const rows = trades.map(t => [
            t.trade_id,
            t.symbol,
            t.side,
            new Date(t.entry_time).toISOString(),
            new Date(t.exit_time).toISOString(),
            t.entry_price,
            t.exit_price,
            t.quantity,
            t.pnl_net,
            t.commission || 0,
            t.mae || 0,
            t.mfe || 0,
            t.duration_seconds || 0,
            t.regime_trend || '',
            t.regime_volatility || '',
            t.setup_tag || ''
        ])

        // Create CSV content
        const csvContent = [
            headers.join(','),
            ...rows.map(row => row.join(','))
        ].join('\n')

        // Download
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `trades_export_${new Date().toISOString().split('T')[0]}.csv`
        link.click()
    }

    const exportToJSON = () => {
        if (!trades.length) return

        const exportData = {
            export_date: new Date().toISOString(),
            strategy_id: "DEMO_STRAT",
            summary: stats,
            trades: trades
        }

        const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `strategy_report_${new Date().toISOString().split('T')[0]}.json`
        link.click()
    }

    const generateSummaryReport = () => {
        if (!stats) return

        const reportContent = `
STRATEGY ANALYSIS REPORT
========================
Generated: ${new Date().toLocaleString()}

PERFORMANCE SUMMARY
-------------------
Total Trades: ${stats.total_trades}
Win Rate: ${stats.win_rate}%
Profit Factor: ${stats.profit_factor}
Average Trade: ${stats.average_trade} €
Max Drawdown: ${stats.max_drawdown} €
Net Profit: ${stats.net_profit} €

TRADE BREAKDOWN
---------------
Winning Trades: ${trades.filter(t => t.pnl_net > 0).length}
Losing Trades: ${trades.filter(t => t.pnl_net <= 0).length}
Largest Win: ${Math.max(...trades.map(t => t.pnl_net)).toFixed(2)} €
Largest Loss: ${Math.min(...trades.map(t => t.pnl_net)).toFixed(2)} €

REGIME ANALYSIS
---------------
${trades.filter(t => t.regime_trend === 'BULL').length} trades in BULL trend
${trades.filter(t => t.regime_trend === 'BEAR').length} trades in BEAR trend
${trades.filter(t => t.regime_trend === 'RANGE').length} trades in RANGE

VOLATILITY BREAKDOWN
--------------------
${trades.filter(t => t.regime_volatility === 'HIGH').length} trades in HIGH volatility
${trades.filter(t => t.regime_volatility === 'NORMAL').length} trades in NORMAL volatility
${trades.filter(t => t.regime_volatility === 'LOW').length} trades in LOW volatility
    `.trim()

        const blob = new Blob([reportContent], { type: 'text/plain' })
        const link = document.createElement('a')
        link.href = URL.createObjectURL(blob)
        link.download = `summary_report_${new Date().toISOString().split('T')[0]}.txt`
        link.click()
    }

    if (loading) return <div className="loading">Loading reports...</div>

    return (
        <div className="reports-container">
            <div className="reports-header">
                <h2>Reports & Export</h2>
                <FileText size={24} color="#38bdf8" />
            </div>

            {/* Export Options */}
            <div className="export-grid">
                <div className="card export-card">
                    <div className="export-icon">
                        <Table size={48} color="#4ade80" />
                    </div>
                    <h3>Export to CSV</h3>
                    <p>Export all trade data in CSV format for Excel or other spreadsheet applications.</p>
                    <button className="btn-primary" onClick={exportToCSV}>
                        <Download size={16} /> Export CSV
                    </button>
                </div>

                <div className="card export-card">
                    <div className="export-icon">
                        <BarChart3 size={48} color="#38bdf8" />
                    </div>
                    <h3>Export to JSON</h3>
                    <p>Export complete strategy data including trades and statistics in JSON format.</p>
                    <button className="btn-primary" onClick={exportToJSON}>
                        <Download size={16} /> Export JSON
                    </button>
                </div>

                <div className="card export-card">
                    <div className="export-icon">
                        <FileText size={48} color="#fbbf24" />
                    </div>
                    <h3>Summary Report</h3>
                    <p>Generate a text summary report with key performance metrics and breakdowns.</p>
                    <button className="btn-primary" onClick={generateSummaryReport}>
                        <Download size={16} /> Generate Report
                    </button>
                </div>
            </div>

            {/* Statistics Summary */}
            {stats && (
                <div className="card">
                    <h3>Strategy Statistics</h3>
                    <div className="stats-grid">
                        <div className="stat-box">
                            <div className="stat-label">Total Trades</div>
                            <div className="stat-value">{stats.total_trades}</div>
                        </div>
                        <div className="stat-box">
                            <div className="stat-label">Win Rate</div>
                            <div className="stat-value">{stats.win_rate}%</div>
                        </div>
                        <div className="stat-box">
                            <div className="stat-label">Profit Factor</div>
                            <div className="stat-value">{stats.profit_factor}</div>
                        </div>
                        <div className="stat-box">
                            <div className="stat-label">Average Trade</div>
                            <div className={`stat-value ${stats.average_trade >= 0 ? 'text-success' : 'text-danger'}`}>
                                {stats.average_trade} €
                            </div>
                        </div>
                        <div className="stat-box">
                            <div className="stat-label">Max Drawdown</div>
                            <div className="stat-value text-danger">{stats.max_drawdown} €</div>
                        </div>
                        <div className="stat-box">
                            <div className="stat-label">Net Profit</div>
                            <div className={`stat-value ${stats.net_profit >= 0 ? 'text-success' : 'text-danger'}`}>
                                {stats.net_profit} €
                            </div>
                        </div>
                    </div>
                </div>
            )}

            {/* Data Preview */}
            <div className="card">
                <h3>Data Preview ({trades.length} trades)</h3>
                <div className="table-container">
                    <table className="trades-table">
                        <thead>
                            <tr>
                                <th>ID</th>
                                <th>Symbol</th>
                                <th>Side</th>
                                <th className="text-right">PnL</th>
                                <th>Regime</th>
                                <th>Setup</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trades.slice(0, 10).map((trade) => (
                                <tr key={trade.trade_id} className="trade-row">
                                    <td className="font-mono text-sm">{trade.trade_id.substring(0, 8)}...</td>
                                    <td>{trade.symbol}</td>
                                    <td>
                                        <span className={`badge ${trade.side === 'BUY' ? 'badge-long' : 'badge-short'}`}>
                                            {trade.side}
                                        </span>
                                    </td>
                                    <td className={`text-right font-bold ${trade.pnl_net >= 0 ? 'text-success' : 'text-danger'}`}>
                                        {trade.pnl_net.toFixed(2)} €
                                    </td>
                                    <td className="text-sm">{trade.regime_trend || '-'} / {trade.regime_volatility || '-'}</td>
                                    <td className="text-sm">{trade.setup_tag || 'Untagged'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {trades.length > 10 && (
                        <div className="table-footer">
                            Showing 10 of {trades.length} trades
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}

export default Reports
