import React, { useState, useEffect } from 'react';
import { Key, Plus, Trash2, Copy, Check, AlertTriangle, X } from 'lucide-react';
import api from '../../../api/axios';

const ApiKeysSection = () => {
    const [keys, setKeys] = useState([]);
    const [loading, setLoading] = useState(true);
    const [generating, setGenerating] = useState(false);
    const [copiedId, setCopiedId] = useState(null);
    const [params, setParams] = useState({ label: '', scopes: ['connections:read', 'connections:write'] }); // Default scopes
    const [newKey, setNewKey] = useState(null); // To store the raw key after creation
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchKeys();
    }, []);

    const fetchKeys = async () => {
        try {
            const response = await api.get('/auth/api-keys');
            setKeys(response.data);
        } catch (err) {
            console.error("Failed to fetch API keys", err);
        } finally {
            setLoading(false);
        }
    };

    const handleCreate = async () => {
        setGenerating(true);
        setError(null);
        try {
            // Default label if empty
            const label = params.label || `Key-${Date.now()}`;
            const payload = {
                label: label,
                scopes: params.scopes
            };
            const response = await api.post('/auth/api-keys', payload);
            setNewKey(response.data); // Contains raw 'api_key'
            setParams({ label: '', scopes: ['connections:read', 'connections:write'] });
            fetchKeys();
        } catch (err) {
            setError("Failed to create API key");
            console.error(err);
        } finally {
            setGenerating(false);
        }
    };

    const handleDelete = async (id) => {
        if (!window.confirm("Are you sure you want to revoke this key? This action cannot be undone.")) return;
        try {
            await api.delete(`/auth/api-keys/${id}`);
            setKeys(keys.filter(k => k.key_id !== id));
        } catch (err) {
            console.error("Failed to revoke key", err);
        }
    };

    const handleCopy = (text, id = null) => {
        navigator.clipboard.writeText(text);
        if (id) {
            setCopiedId(id);
            setTimeout(() => setCopiedId(null), 2000);
        }
    };

    return (
        <div className="space-y-8 animate-fade-in relative">

            {/* New Key Modal overlay */}
            {newKey && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
                    <div className="bg-slate-900 border border-slate-700 p-6 rounded-2xl shadow-2xl max-w-lg w-full transform transition-all scale-100">
                        <div className="flex justify-between items-start mb-4">
                            <div className="flex items-center gap-3 text-green-400">
                                <Check size={24} />
                                <h3 className="text-xl font-bold text-white">API Key Created</h3>
                            </div>
                            <button onClick={() => setNewKey(null)} className="text-slate-500 hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        </div>

                        <div className="space-y-4">
                            <p className="text-slate-300 text-sm">
                                This is the only time you will see this key. Please copy it and store it somewhere safe.
                            </p>

                            <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 break-all font-mono text-green-400 text-sm flex items-center justify-between gap-4">
                                <span>{newKey.api_key}</span>
                                <button
                                    onClick={() => handleCopy(newKey.api_key, 'new')}
                                    className="p-2 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-white transition-colors flex-shrink-0"
                                >
                                    {copiedId === 'new' ? <Check size={18} /> : <Copy size={18} />}
                                </button>
                            </div>

                            <div className="bg-orange-900/20 border border-orange-900/50 p-3 rounded-lg flex gap-3 text-orange-200/80 text-xs">
                                <AlertTriangle size={16} className="flex-shrink-0" />
                                <p>You will not be able to view this secret key again once you close this window.</p>
                            </div>

                            <button
                                onClick={() => setNewKey(null)}
                                className="w-full py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg font-medium transition-colors"
                            >
                                I have saved my key
                            </button>
                        </div>
                    </div>
                </div>
            )}

            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="p-3 rounded-lg bg-orange-500/10 border border-orange-500/20 text-orange-400">
                        <Key size={24} />
                    </div>
                    <div>
                        <h3 className="text-lg font-semibold text-white">API Keys</h3>
                        <p className="text-sm text-slate-400">Manage API keys for external access.</p>
                    </div>
                </div>

                {/* Simple Creator */}
                <div className="flex gap-2">
                    <input
                        type="text"
                        placeholder="Key Label (Optional)"
                        className="bg-slate-900/50 border border-slate-700 rounded-lg px-3 py-1.5 text-sm text-white focus:ring-1 focus:ring-orange-500 outline-none"
                        value={params.label}
                        onChange={(e) => setParams({ ...params, label: e.target.value })}
                    />
                    <button
                        onClick={handleCreate}
                        disabled={generating}
                        className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-500 disabled:opacity-50 text-white rounded-lg font-medium transition-colors shadow-lg shadow-orange-600/20"
                    >
                        {generating ? '...' : <><Plus size={18} /> Generate New Key</>}
                    </button>
                </div>
            </div>

            <div className="space-y-4">
                {error && <div className="text-red-400 text-sm bg-red-900/10 p-2 rounded border border-red-900/20">{error}</div>}

                {loading ? (
                    <div className="text-slate-500 text-center py-8">Loading keys...</div>
                ) : (
                    <>
                        {keys.map((key) => (
                            <div key={key.key_id} className="p-4 rounded-xl bg-slate-900/40 border border-slate-700/50 backdrop-blur-sm flex items-center justify-between group hover:border-slate-600 transition-colors">
                                <div className="flex items-center gap-4">
                                    <div className="w-10 h-10 rounded-full bg-slate-800 flex items-center justify-center text-slate-400">
                                        <Key size={18} />
                                    </div>
                                    <div>
                                        <h4 className="font-medium text-slate-200">{key.label || 'Untitled Key'}</h4>
                                        <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                                            <span className="font-mono bg-slate-950 px-1.5 py-0.5 rounded border border-slate-800">
                                                ID: {key.key_id ? `${key.key_id.substring(0, 8)}...` : 'Unknown'}
                                            </span>
                                            {key.expires_utc && <span>• Expires {new Date(key.expires_utc).toLocaleDateString()}</span>}
                                            {/* <span>• Created {key.created}</span> */}
                                        </div>
                                    </div>
                                </div>

                                <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <button
                                        onClick={() => handleDelete(key.key_id)}
                                        className="p-2 rounded-lg hover:bg-red-500/10 text-slate-400 hover:text-red-500 transition-colors"
                                        title="Revoke Key"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                </div>
                            </div>
                        ))}

                        {keys.length === 0 && (
                            <div className="text-center py-12 border-2 border-dashed border-slate-800 rounded-xl">
                                <p className="text-slate-500">No API keys active.</p>
                            </div>
                        )}
                    </>
                )}

                <div className="mt-6 p-4 rounded-lg bg-blue-500/5 border border-blue-500/20 text-sm text-blue-300">
                    <p>
                        <strong>Note:</strong> API keys allow external applications to access your Quant Lab data.
                        Keep them secure and do not share them with anyone.
                    </p>
                </div>
            </div>
        </div>
    );
};

export default ApiKeysSection;
