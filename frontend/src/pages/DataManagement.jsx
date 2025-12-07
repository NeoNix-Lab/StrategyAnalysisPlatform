import { useState } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle, Loader } from 'lucide-react'
import './DataManagement.css'

const DataManagement = () => {
    const [dragActive, setDragActive] = useState(false)
    const [file, setFile] = useState(null)
    const [uploadStatus, setUploadStatus] = useState('idle') // idle, uploading, success, error
    const [message, setMessage] = useState('')

    const handleDrag = (e) => {
        e.preventDefault()
        e.stopPropagation()
        if (e.type === 'dragenter' || e.type === 'dragover') {
            setDragActive(true)
        } else if (e.type === 'dragleave') {
            setDragActive(false)
        }
    }

    const handleDrop = (e) => {
        e.preventDefault()
        e.stopPropagation()
        setDragActive(false)
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFile(e.dataTransfer.files[0])
        }
    }

    const handleChange = (e) => {
        e.preventDefault()
        if (e.target.files && e.target.files[0]) {
            handleFile(e.target.files[0])
        }
    }

    const handleFile = (file) => {
        if (file.name.endsWith('.sqlite') || file.name.endsWith('.db')) {
            setFile(file)
            setUploadStatus('idle')
            setMessage('')
        } else {
            setUploadStatus('error')
            setMessage('Invalid file type. Please upload a .sqlite or .db file.')
        }
    }

    const uploadFile = async () => {
        if (!file) return

        setUploadStatus('uploading')
        const formData = new FormData()
        formData.append('file', file)

        try {
            const response = await fetch('http://localhost:8000/api/ingest/upload', {
                method: 'POST',
                body: formData,
            })

            if (response.ok) {
                const data = await response.json()
                setUploadStatus('success')
                setMessage(`Success! ${data.message}`)
                setFile(null)
            } else {
                setUploadStatus('error')
                setMessage('Upload failed. Please try again.')
            }
        } catch (error) {
            setUploadStatus('error')
            setMessage(`Error: ${error.message}`)
        }
    }

    return (
        <div className="data-management-container">
            <div className="page-header">
                <h1>Data Management</h1>
                <p>Upload strategy export files (.sqlite) to ingest data into the platform.</p>
            </div>

            <div className="upload-section">
                <div
                    className={`drop-zone ${dragActive ? 'active' : ''}`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                >
                    <input
                        type="file"
                        id="file-upload"
                        className="file-input"
                        onChange={handleChange}
                        accept=".sqlite,.db"
                    />
                    <label htmlFor="file-upload" className="file-label">
                        <div className="icon-wrapper">
                            <Upload size={48} />
                        </div>
                        <span className="drop-text">Drag & Drop your .sqlite file here</span>
                        <span className="or-text">or click to browse</span>
                    </label>
                </div>

                {file && (
                    <div className="file-preview">
                        <div className="file-info">
                            <FileText size={24} />
                            <span className="file-name">{file.name}</span>
                            <span className="file-size">{(file.size / 1024 / 1024).toFixed(2)} MB</span>
                        </div>
                        <button
                            className="upload-btn"
                            onClick={uploadFile}
                            disabled={uploadStatus === 'uploading'}
                        >
                            {uploadStatus === 'uploading' ? (
                                <>
                                    <Loader className="spin" size={18} /> Uploading...
                                </>
                            ) : (
                                'Start Import'
                            )}
                        </button>
                    </div>
                )}

                {uploadStatus === 'success' && (
                    <div className="status-message success">
                        <CheckCircle size={20} />
                        <span>{message}</span>
                    </div>
                )}

                {uploadStatus === 'error' && (
                    <div className="status-message error">
                        <AlertCircle size={20} />
                        <span>{message}</span>
                    </div>
                )}
            </div>

            {/* Placeholder for Import History */}
            <div className="history-section">
                <h2>Import History</h2>
                <div className="empty-state">
                    <p>No import history available yet.</p>
                </div>
            </div>
        </div>
    )
}

export default DataManagement
