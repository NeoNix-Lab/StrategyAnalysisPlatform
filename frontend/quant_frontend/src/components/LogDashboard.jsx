import React, { useState, useEffect, useRef } from 'react';
import { Terminal, X, Pause, Play, Trash2, Maximize2, Minimize2 } from 'lucide-react';

const LogDashboard = () => {
    const [isOpen, setIsOpen] = useState(false);
    const [logs, setLogs] = useState([]);
    const [isPaused, setIsPaused] = useState(false);
    const ws = useRef(null);
    const logsEndRef = useRef(null);
    const [isMaximized, setIsMaximized] = useState(false);

    useEffect(() => {
        if (isOpen) {
            connect();
        } else {
            disconnect();
        }
        return () => disconnect();
    }, [isOpen]);

    useEffect(() => {
        if (!isPaused && logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
        }
    }, [logs, isPaused]);

    const connect = () => {
        if (ws.current) return;

        // Determine WS URL relative to current host
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        // Development proxy often forwards /api so we use that path logic or explicit proxy
        // Assuming frontend proxy forwards /api -> backend:8000
        // But websockets might need direct port or correct proxy setup
        // Let's try relative path assuming setup handles it, or fallback
        const wsUrl = `${protocol}//${window.location.host}/api/system/ws/logs`;
        // Or if running purely local dev separate ports:
        // const wsUrl = 'ws://localhost:8000/api/system/ws/logs'; 

        // For now, let's use relative path which is robust with proxy

        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
            addSystemLog('Connected to Log Stream', 'INFO');
        };

        ws.current.onmessage = (event) => {
            if (isPaused) return;
            try {
                const log = JSON.parse(event.data);
                // log = { timestamp, level, name, message }
                setLogs(prev => [...prev.slice(-999), log]); // Keep last 1000
            } catch (e) {
                console.error("Failed to parse log", e);
            }
        };

        ws.current.onclose = () => {
            addSystemLog('Disconnected from Log Stream', 'WARNING');
            ws.current = null;
        };

        ws.current.onerror = (err) => {
            addSystemLog('WebSocket Error', 'ERROR');
            console.error(err);
        };
    };

    const disconnect = () => {
        if (ws.current) {
            ws.current.close();
            ws.current = null;
        }
    };

    const addSystemLog = (msg, level) => {
        setLogs(prev => [...prev, {
            timestamp: new Date().toISOString(),
            level,
            name: 'System',
            message: msg
        }]);
    };

    const clearLogs = () => setLogs([]);

    const getLevelColor = (level) => {
        switch (level) {
            case 'INFO': return '#3b82f6';
            case 'WARNING': return '#eab308';
            case 'ERROR': return '#ef4444';
            case 'CRITICAL': return '#dc2626';
            case 'DEBUG': return '#a855f7';
            default: return '#94a3b8';
        }
    };

    if (!isOpen) {
        return (
            <button
                onClick={() => setIsOpen(true)}
                style={{
                    position: 'fixed',
                    bottom: '20px',
                    right: '20px',
                    background: '#0f172a',
                    border: '1px solid #334155',
                    borderRadius: '50%',
                    width: '50px',
                    height: '50px',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: '#e2e8f0',
                    cursor: 'pointer',
                    zIndex: 9999,
                    boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                }}
                title="Open Log Dashboard"
            >
                <Terminal size={24} />
            </button>
        );
    }

    return (
        <div style={{
            position: 'fixed',
            bottom: '20px',
            right: '20px',
            width: isMaximized ? 'calc(100vw - 40px)' : '600px',
            height: isMaximized ? 'calc(100vh - 40px)' : '400px',
            background: '#0f172a',
            border: '1px solid #334155',
            borderRadius: '0.5rem',
            display: 'flex',
            flexDirection: 'column',
            zIndex: 9999,
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            transition: 'width 0.2s, height 0.2s'
        }}>
            <div style={{
                padding: '0.75rem',
                borderBottom: '1px solid #334155',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                background: '#1e293b',
                borderTopLeftRadius: '0.5rem',
                borderTopRightRadius: '0.5rem'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600, color: '#e2e8f0' }}>
                    <Terminal size={16} />
                    <span>System Logs</span>
                    <span style={{ fontSize: '0.75rem', fontWeight: 400, color: '#94a3b8', marginLeft: '0.5rem' }}>
                        {logs.length} events
                    </span>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    <button onClick={clearLogs} className="icon-btn" title="Clear Logs"><Trash2 size={14} /></button>
                    <button onClick={() => setIsPaused(!isPaused)} className="icon-btn" title={isPaused ? "Resume" : "Pause"}>
                        {isPaused ? <Play size={14} /> : <Pause size={14} />}
                    </button>
                    <button onClick={() => setIsMaximized(!isMaximized)} className="icon-btn" title="Maximize">
                        {isMaximized ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                    </button>
                    <button onClick={() => setIsOpen(false)} className="icon-btn" title="Close"><X size={14} /></button>
                </div>
            </div>

            <div style={{
                flex: 1,
                overflowY: 'auto',
                padding: '0.5rem',
                fontFamily: `'Fira Code', monospace`,
                fontSize: '0.75rem',
                color: '#e2e8f0',
                background: '#020617'
            }}>
                {logs.map((log, i) => (
                    <div key={i} style={{
                        display: 'flex',
                        gap: '0.5rem',
                        padding: '0.125rem 0',
                        borderBottom: '1px solid #1e293b80',
                        opacity: isPaused && i >= logs.length - 1 ? 0.5 : 1
                    }}>
                        <span style={{ color: '#64748b', minWidth: '140px', userSelect: 'none' }}>
                            {log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : '--:--:--'}
                        </span>
                        <span style={{
                            color: getLevelColor(log.level),
                            fontWeight: 600,
                            minWidth: '60px',
                            userSelect: 'none'
                        }}>
                            {log.level}
                        </span>
                        <span style={{ color: '#94a3b8', minWidth: '120px', userSelect: 'none' }}>
                            [{log.name}]
                        </span>
                        <div style={{ display: 'flex', flexDirection: 'column', flex: 1 }}>
                            <span style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>
                                {log.message}
                            </span>
                            {log.meta && Object.keys(log.meta).length > 0 && (
                                <span style={{ fontSize: '0.7rem', color: '#64748b', marginTop: '2px' }}>
                                    {JSON.stringify(log.meta)}
                                </span>
                            )}
                        </div>
                    </div>
                ))}
                <div ref={logsEndRef} />
            </div>

            <style>{`
                .icon-btn {
                    background: transparent;
                    border: none;
                    color: #94a3b8;
                    cursor: pointer;
                    padding: 4px;
                    border-radius: 4px;
                }
                .icon-btn:hover {
                    background: #334155;
                    color: white;
                }
            `}</style>
        </div>
    );
};

export default LogDashboard;
