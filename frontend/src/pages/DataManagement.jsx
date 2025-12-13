import React from 'react'
import { Database, CheckCircle, XCircle } from 'lucide-react'
import './DataManagement.css'

const DataManagement = () => {
    return (
        <div className="data-management-container">
            <div className="card">
                <h2>System Status</h2>
                <div className="status-grid">
                    <div className="status-item">
                        <div className="status-label">Backend V2 (Event-First)</div>
                        <div className="status-value success"><CheckCircle size={16} /> Active</div>
                    </div>
                    <div className="status-item">
                        <div className="status-label">Ingestion API</div>
                        <div className="status-value success"><CheckCircle size={16} /> Online</div>
                    </div>
                    <div className="status-item">
                        <div className="status-label">Legacy Importer</div>
                        <div className="status-value warning"><XCircle size={16} /> Disabled</div>
                    </div>
                </div>
            </div>

            <div className="card">
                <h3>V2 Data Pipeline</h3>
                <p className="description">
                    The platform now accepts real-time events from <b>Quantower</b>.
                    File uploads are currently disabled while the <b>SqliteImporter</b> is being rewritten for the V2 schema.
                </p>
                <div className="pipeline-steps">
                    <div className="step active">1. Strategy Generates Event</div>
                    <div className="step active">2. C# Exporter sends DTO</div>
                    <div className="step active">3. Pydantic Validation</div>
                    <div className="step active">4. DB Storage (Postgres/SQLite)</div>
                    <div className="step pending">5. Analytics Processing (PnL)</div>
                </div>
            </div>
        </div>
    )
}

export default DataManagement
