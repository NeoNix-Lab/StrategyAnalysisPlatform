import React, { useEffect, useMemo, useState } from 'react'
import {
    AlertTriangle,
    CheckCircle2,
    Copy,
    KeyRound,
    Plus,
    Plug,
    RefreshCw,
    Search,
    ShieldCheck,
    Trash2,
    Wifi,
    XCircle,
} from 'lucide-react'
import api from '../api/axios'

const STATUS_STYLES = {
    CONNECTED: 'bg-emerald-500/10 text-emerald-300 border-emerald-500/30',
    DISCONNECTED: 'bg-slate-500/10 text-slate-300 border-slate-500/30',
    ERROR: 'bg-rose-500/10 text-rose-300 border-rose-500/30',
    PENDING: 'bg-amber-500/10 text-amber-300 border-amber-500/30',
    DISABLED: 'bg-slate-700/30 text-slate-400 border-slate-600/40',
}

const MODE_STYLES = {
    LIVE: 'bg-rose-500/10 text-rose-300 border-rose-500/30',
    PAPER: 'bg-sky-500/10 text-sky-300 border-sky-500/30',
}

const STATUS_OPTIONS = ['PENDING', 'CONNECTED', 'DISCONNECTED', 'ERROR', 'DISABLED']
const MODE_OPTIONS = ['LIVE', 'PAPER']
const CAPABILITIES = [
    { key: 'market_data', label: 'Market Data' },
    { key: 'trading', label: 'Trading' },
    { key: 'positions', label: 'Positions' },
    { key: 'account', label: 'Account' },
]

const createDefaultCapabilities = () =>
    CAPABILITIES.reduce((acc, item) => ({ ...acc, [item.key]: item.key !== 'trading' }), {})

const formatDate = (value) => {
    if (!value) return 'n/a'
    const date = new Date(value)
    if (Number.isNaN(date.getTime())) return 'n/a'
    return date.toLocaleString()
}

const parseJsonField = (value, label) => {
    if (!value || !value.trim()) return { value: undefined, error: null }
    try {
        return { value: JSON.parse(value), error: null }
    } catch (err) {
        return { value: undefined, error: `${label} must be valid JSON.` }
    }
}

const Connections = () => {
    const [connections, setConnections] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [searchTerm, setSearchTerm] = useState('')
    const [statusFilter, setStatusFilter] = useState('ALL')
    const [platformFilter, setPlatformFilter] = useState('ALL')
    const [selectedId, setSelectedId] = useState(null)
    const [editing, setEditing] = useState(false)
    const [editError, setEditError] = useState(null)
    const [editForm, setEditForm] = useState({
        name: '',
        platform: '',
        mode: 'LIVE',
        status: 'PENDING',
        account_id: '',
        capabilities: createDefaultCapabilities(),
        config_json: '',
        meta_json: '',
    })
    const [updatingId, setUpdatingId] = useState(null)
    const [heartbeatLatency, setHeartbeatLatency] = useState('')

    const [creating, setCreating] = useState(false)
    const [formError, setFormError] = useState(null)
    const [form, setForm] = useState({
        name: '',
        platform: 'BINANCE',
        mode: 'LIVE',
        status: 'PENDING',
        account_id: '',
        capabilities: createDefaultCapabilities(),
        config_json: '',
        meta_json: '',
        secrets_json: '',
    })

    const [apiKeys, setApiKeys] = useState([])
    const [apiKeyForm, setApiKeyForm] = useState({
        label: '',
        expires: '',
        scopes: {
            'connections:read': true,
            'connections:write': true,
            'ingest:write': false,
            'trading:read': false,
            'trading:write': false,
        },
    })
    const [apiKeyLoading, setApiKeyLoading] = useState(false)
    const [apiKeyError, setApiKeyError] = useState(null)
    const [latestKey, setLatestKey] = useState(null)

    const fetchConnections = async () => {
        setLoading(true)
        setError(null)
        try {
            const response = await api.get('/connections')
            const payload = response.data || []
            setConnections(payload)
            setSelectedId((current) => {
                if (current && payload.some((c) => c.connection_id === current)) {
                    return current
                }
                return payload[0]?.connection_id ?? null
            })
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Failed to load connections')
        } finally {
            setLoading(false)
        }
    }

    const fetchApiKeys = async () => {
        try {
            const response = await api.get('/auth/api-keys')
            setApiKeys(response.data || [])
        } catch (err) {
            setApiKeys([])
        }
    }

    useEffect(() => {
        fetchConnections()
        fetchApiKeys()
    }, [])

    const selectedConnection = useMemo(
        () => connections.find((item) => item.connection_id === selectedId) || null,
        [connections, selectedId]
    )

    useEffect(() => {
        if (!selectedConnection) return
        setEditing(false)
        setEditError(null)
        setHeartbeatLatency('')
        setEditForm({
            name: selectedConnection.name || '',
            platform: selectedConnection.platform || '',
            mode: selectedConnection.mode || 'LIVE',
            status: selectedConnection.status || 'PENDING',
            account_id: selectedConnection.account_id || '',
            capabilities: selectedConnection.capabilities_json || createDefaultCapabilities(),
            config_json: selectedConnection.config_json ? JSON.stringify(selectedConnection.config_json, null, 2) : '',
            meta_json: selectedConnection.meta_json ? JSON.stringify(selectedConnection.meta_json, null, 2) : '',
        })
    }, [selectedConnection])

    const filteredConnections = useMemo(() => {
        const term = searchTerm.trim().toLowerCase()
        return connections.filter((conn) => {
            if (statusFilter !== 'ALL' && conn.status !== statusFilter) return false
            if (platformFilter !== 'ALL' && conn.platform !== platformFilter) return false
            if (!term) return true
            const haystack = `${conn.name || ''} ${conn.platform || ''} ${conn.connection_id || ''} ${
                conn.account_id || ''
            }`.toLowerCase()
            return haystack.includes(term)
        })
    }, [connections, searchTerm, statusFilter, platformFilter])

    const platformOptions = useMemo(() => {
        const platforms = Array.from(new Set(connections.map((c) => c.platform).filter(Boolean)))
        return ['ALL', ...platforms]
    }, [connections])

    const stats = useMemo(() => {
        const total = connections.length
        const connected = connections.filter((c) => c.status === 'CONNECTED').length
        const issues = connections.filter((c) => ['ERROR', 'DISCONNECTED'].includes(c.status)).length
        return { total, connected, issues }
    }, [connections])

    const handleCreate = async () => {
        setFormError(null)
        const configResult = parseJsonField(form.config_json, 'Config JSON')
        if (configResult.error) return setFormError(configResult.error)
        const metaResult = parseJsonField(form.meta_json, 'Meta JSON')
        if (metaResult.error) return setFormError(metaResult.error)
        const secretsResult = parseJsonField(form.secrets_json, 'Secrets JSON')
        if (secretsResult.error) return setFormError(secretsResult.error)

        const payload = {
            name: form.name || null,
            platform: form.platform,
            mode: form.mode,
            status: form.status,
            account_id: form.account_id || null,
            capabilities_json: form.capabilities,
        }
        if (configResult.value !== undefined) payload.config_json = configResult.value
        if (metaResult.value !== undefined) payload.meta_json = metaResult.value
        if (secretsResult.value !== undefined) payload.secrets_json = secretsResult.value

        setCreating(true)
        try {
            await api.post('/connections', payload)
            await fetchConnections()
            setForm({
                name: '',
                platform: 'BINANCE',
                mode: 'LIVE',
                status: 'PENDING',
                account_id: '',
                capabilities: createDefaultCapabilities(),
                config_json: '',
                meta_json: '',
                secrets_json: '',
            })
        } catch (err) {
            setFormError(err.response?.data?.detail || err.message || 'Failed to create connection')
        } finally {
            setCreating(false)
        }
    }

    const updateConnection = async (connectionId, payload) => {
        setUpdatingId(connectionId)
        try {
            await api.patch(`/connections/${connectionId}`, payload)
            await fetchConnections()
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Failed to update connection')
        } finally {
            setUpdatingId(null)
        }
    }

    const updateStatus = async (connectionId, status) => {
        await updateConnection(connectionId, { status })
    }

    const sendHeartbeat = async (connectionId) => {
        setUpdatingId(connectionId)
        try {
            await api.post(`/connections/${connectionId}/heartbeat`, {})
            await fetchConnections()
        } catch (err) {
            setError(err.response?.data?.detail || err.message || 'Failed to send heartbeat')
        } finally {
            setUpdatingId(null)
        }
    }

    const handleSaveEdit = async () => {
        if (!selectedConnection) return
        setEditError(null)
        const configResult = parseJsonField(editForm.config_json, 'Config JSON')
        if (configResult.error) return setEditError(configResult.error)
        const metaResult = parseJsonField(editForm.meta_json, 'Meta JSON')
        if (metaResult.error) return setEditError(metaResult.error)

        const payload = {
            name: editForm.name || null,
            platform: editForm.platform || null,
            mode: editForm.mode,
            status: editForm.status,
            account_id: editForm.account_id || null,
            capabilities_json: editForm.capabilities,
        }

        if (configResult.value !== undefined) payload.config_json = configResult.value
        if (metaResult.value !== undefined) payload.meta_json = metaResult.value

        await updateConnection(selectedConnection.connection_id, payload)
        setEditing(false)
    }

    const handleHeartbeat = async () => {
        if (!selectedConnection) return
        const payload = {}
        if (heartbeatLatency) payload.latency_ms = Number(heartbeatLatency)
        setUpdatingId(selectedConnection.connection_id)
        try {
            await api.post(`/connections/${selectedConnection.connection_id}/heartbeat`, payload)
            await fetchConnections()
        } catch (err) {
            setEditError(err.response?.data?.detail || err.message || 'Failed to send heartbeat')
        } finally {
            setUpdatingId(null)
        }
    }

    const handleCreateApiKey = async () => {
        setApiKeyError(null)
        const scopes = Object.entries(apiKeyForm.scopes)
            .filter(([, enabled]) => enabled)
            .map(([scope]) => scope)
        const payload = {
            label: apiKeyForm.label || null,
            scopes,
        }
        if (apiKeyForm.expires) {
            payload.expires_utc = new Date(apiKeyForm.expires).toISOString()
        }

        setApiKeyLoading(true)
        try {
            const response = await api.post('/auth/api-keys', payload)
            setLatestKey(response.data)
            setApiKeyForm({
                label: '',
                expires: '',
                scopes: {
                    'connections:read': true,
                    'connections:write': true,
                    'ingest:write': false,
                    'trading:read': false,
                    'trading:write': false,
                },
            })
            await fetchApiKeys()
        } catch (err) {
            setApiKeyError(err.response?.data?.detail || err.message || 'Failed to create API key')
        } finally {
            setApiKeyLoading(false)
        }
    }

    const handleRevokeKey = async (keyId) => {
        setApiKeyError(null)
        try {
            await api.delete(`/auth/api-keys/${keyId}`)
            await fetchApiKeys()
        } catch (err) {
            setApiKeyError(err.response?.data?.detail || err.message || 'Failed to revoke API key')
        }
    }

    const handleCopyLatestKey = async () => {
        if (!latestKey?.api_key || !navigator.clipboard) return
        await navigator.clipboard.writeText(latestKey.api_key)
    }

    return (
        <section className="flex flex-col gap-6 h-full font-sans text-slate-100">
            <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4">
                <div>
                    <div className="flex items-center gap-2 text-xs font-bold text-accent tracking-wider uppercase mb-1">
                        <Plug size={14} /> System / Connections
                    </div>
                    <h1 className="text-3xl font-extrabold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
                        Connection Hub
                    </h1>
                    <p className="text-slate-400 mt-1 max-w-2xl">
                        Register and monitor third-party connectors from a single view.
                    </p>
                </div>
                <button
                    type="button"
                    onClick={fetchConnections}
                    disabled={loading}
                    className="btn-secondary bg-slate-800/50 backdrop-blur-sm border-slate-700/50 hover:bg-slate-700/50"
                >
                    <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="card bg-gradient-to-br from-slate-800/40 to-slate-900/40 border-slate-700/50">
                    <p className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Total Connections</p>
                    <p className="text-3xl font-bold text-white">{stats.total}</p>
                </div>
                <div className="card bg-gradient-to-br from-slate-800/40 to-slate-900/40 border-slate-700/50">
                    <p className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Connected</p>
                    <p className="text-3xl font-bold text-white">{stats.connected}</p>
                </div>
                <div className="card bg-gradient-to-br from-slate-800/40 to-slate-900/40 border-slate-700/50">
                    <p className="text-xs uppercase font-bold text-slate-500 tracking-wider mb-2">Issues</p>
                    <p className="text-3xl font-bold text-white">{stats.issues}</p>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="card border-slate-700/50 bg-slate-900/40">
                    <div className="flex items-center justify-between">
                        <h3 className="text-lg font-semibold text-white">Create Connection</h3>
                        <Plus size={16} className="text-accent" />
                    </div>
                    <div className="mt-4 space-y-3">
                        <div className="grid grid-cols-2 gap-3">
                            <div>
                                <label className="text-xs text-slate-500 uppercase">Name</label>
                                <input
                                    value={form.name}
                                    onChange={(e) => setForm((prev) => ({ ...prev, name: e.target.value }))}
                                    className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm"
                                />
                            </div>
                            <div>
                                <label className="text-xs text-slate-500 uppercase">Platform</label>
                                <input
                                    value={form.platform}
                                    onChange={(e) => setForm((prev) => ({ ...prev, platform: e.target.value }))}
                                    className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm"
                                />
                            </div>
                            <div>
                                <label className="text-xs text-slate-500 uppercase">Mode</label>
                                <select
                                    value={form.mode}
                                    onChange={(e) => setForm((prev) => ({ ...prev, mode: e.target.value }))}
                                    className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm"
                                >
                                    {MODE_OPTIONS.map((mode) => (
                                        <option key={mode} value={mode}>
                                            {mode}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div>
                                <label className="text-xs text-slate-500 uppercase">Status</label>
                                <select
                                    value={form.status}
                                    onChange={(e) => setForm((prev) => ({ ...prev, status: e.target.value }))}
                                    className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm"
                                >
                                    {STATUS_OPTIONS.map((status) => (
                                        <option key={status} value={status}>
                                            {status}
                                        </option>
                                    ))}
                                </select>
                            </div>
                            <div className="col-span-2">
                                <label className="text-xs text-slate-500 uppercase">Account ID</label>
                                <input
                                    value={form.account_id}
                                    onChange={(e) => setForm((prev) => ({ ...prev, account_id: e.target.value }))}
                                    className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm"
                                />
                            </div>
                        </div>

                        <div>
                            <label className="text-xs text-slate-500 uppercase">Capabilities</label>
                            <div className="grid grid-cols-2 gap-2 mt-2">
                                {CAPABILITIES.map((capability) => (
                                    <label
                                        key={capability.key}
                                        className={`flex items-center gap-2 px-3 py-2 rounded border text-xs cursor-pointer transition-colors ${
                                            form.capabilities[capability.key]
                                                ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200'
                                                : 'bg-slate-900 border-slate-800 text-slate-500 hover:bg-slate-800'
                                        }`}
                                    >
                                        <input
                                            type="checkbox"
                                            className="sr-only"
                                            checked={!!form.capabilities[capability.key]}
                                            onChange={() =>
                                                setForm((prev) => ({
                                                    ...prev,
                                                    capabilities: {
                                                        ...prev.capabilities,
                                                        [capability.key]: !prev.capabilities[capability.key],
                                                    },
                                                }))
                                            }
                                        />
                                        <span>{capability.label}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        <div>
                            <label className="text-xs text-slate-500 uppercase">Config JSON</label>
                            <textarea
                                value={form.config_json}
                                onChange={(e) => setForm((prev) => ({ ...prev, config_json: e.target.value }))}
                                rows={2}
                                className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm font-mono"
                            />
                        </div>
                        <div>
                            <label className="text-xs text-slate-500 uppercase">Meta JSON</label>
                            <textarea
                                value={form.meta_json}
                                onChange={(e) => setForm((prev) => ({ ...prev, meta_json: e.target.value }))}
                                rows={2}
                                className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm font-mono"
                            />
                        </div>
                        <div>
                            <label className="text-xs text-slate-500 uppercase">Secrets JSON</label>
                            <textarea
                                value={form.secrets_json}
                                onChange={(e) => setForm((prev) => ({ ...prev, secrets_json: e.target.value }))}
                                rows={2}
                                className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm font-mono"
                            />
                            <p className="text-xs text-slate-500 mt-1">Stored encrypted on the backend.</p>
                        </div>

                        {formError && (
                            <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2">
                                {formError}
                            </div>
                        )}

                        <button
                            className="btn-primary text-xs py-2 px-4"
                            onClick={handleCreate}
                            disabled={creating || !form.platform}
                        >
                            {creating ? 'Creating...' : 'Create Connection'}
                        </button>
                    </div>
                </div>

                <div className="lg:col-span-2 flex flex-col min-h-0 card p-0 border-slate-700/50 overflow-hidden bg-slate-900/30">
                    <div className="p-4 border-b border-slate-700/50 flex flex-col md:flex-row gap-3 items-start md:items-center justify-between bg-slate-900/20">
                        <div className="relative flex-1 max-w-md">
                            <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" />
                            <input
                                type="search"
                                placeholder="Search connections..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full bg-slate-900/50 border border-slate-700 rounded-lg py-2 pl-9 pr-4 text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/50 transition-all"
                            />
                        </div>
                        <div className="flex flex-wrap gap-2">
                            <select
                                value={platformFilter}
                                onChange={(e) => setPlatformFilter(e.target.value)}
                                className="bg-slate-900/50 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-accent/50"
                            >
                                {platformOptions.map((platform) => (
                                    <option key={platform} value={platform}>
                                        {platform === 'ALL' ? 'All Platforms' : platform}
                                    </option>
                                ))}
                            </select>
                            <select
                                value={statusFilter}
                                onChange={(e) => setStatusFilter(e.target.value)}
                                className="bg-slate-900/50 border border-slate-700 text-slate-200 text-xs rounded-lg px-3 py-2 focus:outline-none focus:border-accent/50"
                            >
                                <option value="ALL">All Status</option>
                                {STATUS_OPTIONS.map((status) => (
                                    <option key={status} value={status}>
                                        {status}
                                    </option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="flex-1 overflow-y-auto custom-scrollbar">
                        <table className="w-full text-left border-collapse">
                            <thead className="sticky top-0 bg-slate-900/95 backdrop-blur-md z-10 border-b border-slate-700/50 shadow-sm">
                                <tr>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider w-[25%]">
                                        Connection
                                    </th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Mode</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">Status</th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                        Account
                                    </th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider">
                                        Heartbeat
                                    </th>
                                    <th className="py-3 px-4 text-xs font-semibold text-slate-400 uppercase tracking-wider text-right">
                                        Actions
                                    </th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800/50">
                                {filteredConnections.map((conn) => {
                                    const isSelected = conn.connection_id === selectedId
                                    return (
                                        <tr
                                            key={conn.connection_id}
                                            onClick={() => setSelectedId(conn.connection_id)}
                                            className={`cursor-pointer transition-colors ${
                                                isSelected ? 'bg-slate-800/60' : 'hover:bg-slate-800/30'
                                            }`}
                                        >
                                        <td className="py-3 px-4">
                                            <div className="font-semibold text-slate-200">{conn.name || conn.platform}</div>
                                            <div className="text-xs text-slate-500 font-mono">
                                                {conn.connection_id.slice(0, 8)}
                                            </div>
                                        </td>
                                        <td className="py-3 px-4 text-sm">
                                            <span
                                                className={`px-2 py-1 text-xs border rounded-full ${
                                                    MODE_STYLES[conn.mode] || 'border-slate-700 text-slate-400'
                                                }`}
                                            >
                                                {conn.mode}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-sm">
                                            <span
                                                className={`px-2 py-1 text-xs border rounded-full ${
                                                    STATUS_STYLES[conn.status] || 'border-slate-700 text-slate-400'
                                                }`}
                                            >
                                                {conn.status}
                                            </span>
                                        </td>
                                        <td className="py-3 px-4 text-sm text-slate-300">{conn.account_id || 'n/a'}</td>
                                        <td className="py-3 px-4 text-sm text-slate-400">{formatDate(conn.last_heartbeat_utc)}</td>
                                        <td className="py-3 px-4 text-right text-xs">
                                            <div className="flex justify-end gap-2" onClick={(event) => event.stopPropagation()}>
                                                <button
                                                    className="inline-flex items-center justify-center w-7 h-7 rounded-lg border border-slate-700 text-slate-300 hover:border-emerald-400/60 hover:text-emerald-200 transition-colors"
                                                    onClick={() => updateStatus(conn.connection_id, 'CONNECTED')}
                                                    title="Set Connected"
                                                >
                                                    <CheckCircle2 size={12} />
                                                </button>
                                                <button
                                                    className="inline-flex items-center justify-center w-7 h-7 rounded-lg border border-slate-700 text-slate-300 hover:border-slate-400/60 hover:text-slate-100 transition-colors"
                                                    onClick={() => updateStatus(conn.connection_id, 'DISCONNECTED')}
                                                    title="Set Disconnected"
                                                >
                                                    <XCircle size={12} />
                                                </button>
                                                <button
                                                    className="inline-flex items-center justify-center w-7 h-7 rounded-lg border border-slate-700 text-slate-300 hover:border-rose-400/60 hover:text-rose-200 transition-colors"
                                                    onClick={() => updateStatus(conn.connection_id, 'ERROR')}
                                                    title="Flag Error"
                                                >
                                                    <AlertTriangle size={12} />
                                                </button>
                                                <button
                                                    className="inline-flex items-center justify-center w-7 h-7 rounded-lg border border-slate-700 text-slate-300 hover:border-sky-400/60 hover:text-sky-200 transition-colors"
                                                    onClick={() => sendHeartbeat(conn.connection_id)}
                                                    title="Send Heartbeat"
                                                >
                                                    <Wifi size={12} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                )})}
                            </tbody>
                        </table>
                        {!loading && filteredConnections.length === 0 && (
                            <div className="p-8 text-center text-slate-500">No connections found.</div>
                        )}
                    </div>
                </div>
            </div>

            <div className="card border-slate-700/50 bg-slate-900/40">
                {selectedConnection ? (
                    <>
                        <div className="flex items-start justify-between gap-3">
                            <div>
                                <div className="text-xs uppercase text-slate-500 tracking-wider">Selected Connection</div>
                                <h3 className="text-xl font-semibold text-white">
                                    {selectedConnection.name || selectedConnection.platform}
                                </h3>
                                <div className="text-xs text-slate-500 font-mono mt-1">
                                    {selectedConnection.connection_id}
                                </div>
                            </div>
                            <span
                                className={`px-2 py-1 text-xs border rounded-full ${
                                    STATUS_STYLES[selectedConnection.status] || 'border-slate-700 text-slate-400'
                                }`}
                            >
                                {selectedConnection.status}
                            </span>
                        </div>

                        <div className="grid grid-cols-2 gap-3 mt-4 text-sm">
                            <div>
                                <div className="text-xs text-slate-500 uppercase">Platform</div>
                                <div className="text-slate-200">{selectedConnection.platform}</div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500 uppercase">Mode</div>
                                <div className="text-slate-200">{selectedConnection.mode}</div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500 uppercase">Account</div>
                                <div className="text-slate-200">{selectedConnection.account_id || 'n/a'}</div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500 uppercase">Latency</div>
                                <div className="text-slate-200">
                                    {selectedConnection.last_latency_ms ? `${selectedConnection.last_latency_ms} ms` : 'n/a'}
                                </div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500 uppercase">Created</div>
                                <div className="text-slate-200">{formatDate(selectedConnection.created_utc)}</div>
                            </div>
                            <div>
                                <div className="text-xs text-slate-500 uppercase">Heartbeat</div>
                                <div className="text-slate-200">{formatDate(selectedConnection.last_heartbeat_utc)}</div>
                            </div>
                        </div>

                        <div className="mt-4">
                            <div className="text-xs text-slate-500 uppercase mb-2">Capabilities</div>
                            <div className="flex flex-wrap gap-2">
                                {Object.entries(selectedConnection.capabilities_json || {}).length ? (
                                    Object.entries(selectedConnection.capabilities_json).map(([key, value]) => (
                                        <span
                                            key={key}
                                            className={`px-2 py-1 text-xs border rounded-full ${
                                                value
                                                    ? 'border-emerald-500/30 text-emerald-200'
                                                    : 'border-slate-700 text-slate-500'
                                            }`}
                                        >
                                            {key}
                                        </span>
                                    ))
                                ) : (
                                    <span className="text-xs text-slate-500">No capabilities set.</span>
                                )}
                            </div>
                        </div>

                        <div className="mt-4 flex flex-wrap gap-2">
                            <button
                                className="btn-secondary text-xs py-2 px-3"
                                disabled={updatingId === selectedConnection.connection_id}
                                onClick={() => updateConnection(selectedConnection.connection_id, { status: 'CONNECTED' })}
                            >
                                <CheckCircle2 size={14} /> Set Connected
                            </button>
                            <button
                                className="btn-secondary text-xs py-2 px-3"
                                disabled={updatingId === selectedConnection.connection_id}
                                onClick={() => updateConnection(selectedConnection.connection_id, { status: 'DISCONNECTED' })}
                            >
                                <XCircle size={14} /> Set Disconnected
                            </button>
                            <button
                                className="btn-secondary text-xs py-2 px-3"
                                disabled={updatingId === selectedConnection.connection_id}
                                onClick={() => updateConnection(selectedConnection.connection_id, { status: 'ERROR' })}
                            >
                                <AlertTriangle size={14} /> Flag Error
                            </button>
                        </div>

                        <div className="mt-4 flex items-center gap-3">
                            <input
                                type="number"
                                placeholder="Latency (ms)"
                                value={heartbeatLatency}
                                onChange={(e) => setHeartbeatLatency(e.target.value)}
                                className="input-field bg-slate-950 border-slate-700 focus:border-accent w-32 text-sm"
                            />
                            <button
                                className="btn-secondary text-xs py-2 px-3"
                                disabled={updatingId === selectedConnection.connection_id}
                                onClick={handleHeartbeat}
                            >
                                <Wifi size={14} /> Heartbeat
                            </button>
                        </div>

                        <div className="mt-5 border-t border-slate-800 pt-4">
                            <div className="flex items-center justify-between">
                                <h4 className="text-sm font-semibold">Quick Edit</h4>
                                <button
                                    className="text-xs text-accent hover:text-white"
                                    onClick={() => setEditing((prev) => !prev)}
                                >
                                    {editing ? 'Close' : 'Edit'}
                                </button>
                            </div>

                            {editing && (
                                <div className="mt-3 space-y-3">
                                    <div className="grid grid-cols-2 gap-3">
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase">Name</label>
                                            <input
                                                value={editForm.name}
                                                onChange={(e) => setEditForm((prev) => ({ ...prev, name: e.target.value }))}
                                                className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase">Account</label>
                                            <input
                                                value={editForm.account_id}
                                                onChange={(e) => setEditForm((prev) => ({ ...prev, account_id: e.target.value }))}
                                                className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase">Mode</label>
                                            <select
                                                value={editForm.mode}
                                                onChange={(e) => setEditForm((prev) => ({ ...prev, mode: e.target.value }))}
                                                className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm"
                                            >
                                                {MODE_OPTIONS.map((mode) => (
                                                    <option key={mode} value={mode}>
                                                        {mode}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase">Status</label>
                                            <select
                                                value={editForm.status}
                                                onChange={(e) => setEditForm((prev) => ({ ...prev, status: e.target.value }))}
                                                className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm"
                                            >
                                                {STATUS_OPTIONS.map((status) => (
                                                    <option key={status} value={status}>
                                                        {status}
                                                    </option>
                                                ))}
                                            </select>
                                        </div>
                                    </div>

                                    <div>
                                        <label className="text-xs text-slate-500 uppercase">Capabilities</label>
                                        <div className="grid grid-cols-2 gap-2 mt-2">
                                            {CAPABILITIES.map((capability) => (
                                                <label
                                                    key={capability.key}
                                                    className={`flex items-center gap-2 px-3 py-2 rounded border text-xs cursor-pointer transition-colors ${
                                                        editForm.capabilities[capability.key]
                                                            ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-200'
                                                            : 'bg-slate-900 border-slate-800 text-slate-500 hover:bg-slate-800'
                                                    }`}
                                                >
                                                    <input
                                                        type="checkbox"
                                                        className="sr-only"
                                                        checked={!!editForm.capabilities[capability.key]}
                                                        onChange={() =>
                                                            setEditForm((prev) => ({
                                                                ...prev,
                                                                capabilities: {
                                                                    ...prev.capabilities,
                                                                    [capability.key]: !prev.capabilities[capability.key],
                                                                },
                                                            }))
                                                        }
                                                    />
                                                    <span>{capability.label}</span>
                                                </label>
                                            ))}
                                        </div>
                                    </div>

                                    <div className="grid grid-cols-1 gap-3">
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase">Config JSON</label>
                                            <textarea
                                                value={editForm.config_json}
                                                onChange={(e) =>
                                                    setEditForm((prev) => ({ ...prev, config_json: e.target.value }))
                                                }
                                                rows={3}
                                                className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm font-mono"
                                            />
                                        </div>
                                        <div>
                                            <label className="text-xs text-slate-500 uppercase">Meta JSON</label>
                                            <textarea
                                                value={editForm.meta_json}
                                                onChange={(e) =>
                                                    setEditForm((prev) => ({ ...prev, meta_json: e.target.value }))
                                                }
                                                rows={2}
                                                className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm font-mono"
                                            />
                                        </div>
                                    </div>

                                    {editError && (
                                        <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2">
                                            {editError}
                                        </div>
                                    )}

                                    <button
                                        className="btn-primary text-xs py-2 px-4"
                                        onClick={handleSaveEdit}
                                        disabled={updatingId === selectedConnection.connection_id}
                                    >
                                        {updatingId === selectedConnection.connection_id ? 'Saving...' : 'Save Changes'}
                                    </button>
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="text-center text-slate-500 py-8">Select a connection to see details.</div>
                )}
            </div>

            <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <div className="card border-slate-700/50 bg-slate-900/40">
                    <div className="flex items-center justify-between">
                        <div>
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <KeyRound size={18} className="text-accent" /> Create API Key
                            </h3>
                            <p className="text-xs text-slate-500 mt-1">Use scoped keys for external adapters.</p>
                        </div>
                    </div>
                    <div className="mt-4 space-y-3">
                        <div>
                            <label className="text-xs text-slate-500 uppercase">Label</label>
                            <input
                                value={apiKeyForm.label}
                                onChange={(e) => setApiKeyForm((prev) => ({ ...prev, label: e.target.value }))}
                                className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm"
                            />
                        </div>
                        <div>
                            <label className="text-xs text-slate-500 uppercase">Expires</label>
                            <input
                                type="datetime-local"
                                value={apiKeyForm.expires}
                                onChange={(e) => setApiKeyForm((prev) => ({ ...prev, expires: e.target.value }))}
                                className="input-field bg-slate-950 border-slate-700 focus:border-accent text-sm"
                            />
                        </div>
                        <div>
                            <label className="text-xs text-slate-500 uppercase">Scopes</label>
                            <div className="grid grid-cols-2 gap-2 mt-2">
                                {Object.keys(apiKeyForm.scopes).map((scope) => (
                                    <label
                                        key={scope}
                                        className={`flex items-center gap-2 px-3 py-2 rounded border text-xs cursor-pointer transition-colors ${
                                            apiKeyForm.scopes[scope]
                                                ? 'bg-indigo-500/10 border-indigo-500/20 text-indigo-200'
                                                : 'bg-slate-900 border-slate-800 text-slate-500 hover:bg-slate-800'
                                        }`}
                                    >
                                        <input
                                            type="checkbox"
                                            className="sr-only"
                                            checked={apiKeyForm.scopes[scope]}
                                            onChange={() =>
                                                setApiKeyForm((prev) => ({
                                                    ...prev,
                                                    scopes: { ...prev.scopes, [scope]: !prev.scopes[scope] },
                                                }))
                                            }
                                        />
                                        <span>{scope}</span>
                                    </label>
                                ))}
                            </div>
                        </div>

                        {apiKeyError && (
                            <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2">
                                {apiKeyError}
                            </div>
                        )}

                        <button
                            className="btn-primary text-xs py-2 px-4"
                            onClick={handleCreateApiKey}
                            disabled={apiKeyLoading}
                        >
                            {apiKeyLoading ? 'Creating...' : 'Generate Key'}
                        </button>

                        {latestKey?.api_key && (
                            <div className="mt-4 p-3 rounded-lg border border-emerald-500/30 bg-emerald-500/10 text-xs text-emerald-200">
                                <div className="flex items-start justify-between gap-3">
                                    <div>
                                        <div className="font-semibold">New API Key</div>
                                        <div className="font-mono break-all">{latestKey.api_key}</div>
                                    </div>
                                    <button className="text-emerald-200 hover:text-white" onClick={handleCopyLatestKey}>
                                        <Copy size={14} />
                                    </button>
                                </div>
                                <div className="text-[10px] text-emerald-300 mt-2">
                                    Copy now. This key will not be shown again.
                                </div>
                            </div>
                        )}
                    </div>
                </div>

                <div className="card border-slate-700/50 bg-slate-900/40">
                    <div className="flex items-center justify-between">
                        <div>
                            <h3 className="text-lg font-semibold text-white flex items-center gap-2">
                                <ShieldCheck size={18} className="text-accent" /> Existing Keys
                            </h3>
                            <p className="text-xs text-slate-500 mt-1">Rotate keys regularly.</p>
                        </div>
                    </div>

                    <div className="mt-4 space-y-3">
                        {apiKeys.length === 0 && <div className="text-xs text-slate-500">No API keys yet.</div>}

                        {apiKeys.map((key) => (
                            <div
                                key={key.key_id}
                                className="p-3 rounded-lg border border-slate-800 bg-slate-950/50 flex items-start justify-between gap-3"
                            >
                                <div>
                                    <div className="text-sm text-slate-200 font-semibold">{key.label || 'Untitled Key'}</div>
                                    <div className="text-xs text-slate-500 font-mono">{key.key_id}</div>
                                    <div className="text-xs text-slate-400 mt-1">
                                        Expires: {key.expires_utc ? formatDate(key.expires_utc) : 'never'}
                                    </div>
                                    <div className="flex flex-wrap gap-1 mt-2">
                                        {(key.scopes || []).map((scope) => (
                                            <span
                                                key={scope}
                                                className="px-2 py-0.5 text-[10px] rounded-full border border-slate-700 text-slate-400"
                                            >
                                                {scope}
                                            </span>
                                        ))}
                                    </div>
                                </div>
                                <button
                                    className="text-xs text-rose-300 hover:text-rose-200"
                                    onClick={() => handleRevokeKey(key.key_id)}
                                >
                                    <Trash2 size={14} />
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            </div>

            {error && (
                <div className="text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg p-2">
                    {error}
                </div>
            )}
        </section>
    )
}

export default Connections
