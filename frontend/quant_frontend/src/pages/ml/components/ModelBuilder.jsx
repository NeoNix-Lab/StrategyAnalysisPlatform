import React from 'react';
import { Layers, Plus, Trash2, Settings, ArrowDown, Box } from 'lucide-react';

const LAYER_TYPES = [
    { type: 'Dense', default: { units: 64, activation: 'relu' } },
    { type: 'LSTM', default: { units: 64, return_sequences: false } },
    { type: 'Dropout', default: { rate: 0.2 } },
    { type: 'Flatten', default: {} }
];

const ModelBuilder = ({ layers, setLayers }) => {
    const addLayer = (typeDef) => {
        setLayers([...layers, { type: typeDef.type, ...typeDef.default }]);
    };

    const removeLayer = (index) => {
        setLayers(layers.filter((_, i) => i !== index));
    };

    const updateLayer = (index, key, value) => {
        const newLayers = [...layers];
        newLayers[index] = { ...newLayers[index], [key]: value };
        setLayers(newLayers);
    };

    return (
        <div className="flex gap-6 h-full w-full">
            {/* Palette Sidebar */}
            <div className="w-[240px] flex-shrink-0 flex flex-col gap-4">
                <div className="bg-[#0f172a] rounded-xl border border-slate-800 flex flex-col overflow-hidden shadow-lg h-full">
                    <div className="p-4 bg-slate-900/80 border-b border-slate-800 backdrop-blur-sm">
                        <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest flex items-center gap-2">
                            <Box size={14} className="text-violet-500" /> Layer Palette
                        </h3>
                    </div>
                    <div className="p-3 flex flex-col gap-3 overflow-y-auto custom-scrollbar flex-1">
                        {LAYER_TYPES.map(lt => (
                            <button
                                key={lt.type}
                                onClick={() => addLayer(lt)}
                                className="flex items-center justify-between px-4 py-3 bg-[#1e293b]/50 hover:bg-[#1e293b] border border-slate-800 hover:border-slate-600 rounded-lg text-sm text-slate-300 hover:text-white transition-all group shadow-sm text-left"
                            >
                                <span className="font-medium">{lt.type}</span>
                                <Plus size={16} className="opacity-0 group-hover:opacity-100 text-violet-400 transition-opacity" />
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* Canvas / Stack Area */}
            <div className="flex-1 bg-[#020617]/50 rounded-xl border border-dashed border-slate-800/50 p-8 overflow-y-auto relative custom-scrollbar flex flex-col items-center">
                <div className="absolute inset-0 bg-[radial-gradient(#1e293b_1px,transparent_1px)] [background-size:24px_24px] opacity-20 pointer-events-none"></div>

                <div className="w-full max-w-2xl relative z-10 pb-20">

                    {/* Input Node */}
                    <div className="w-full flex justify-center mb-8">
                        <div className="py-2 px-6 rounded-full border border-dashed border-slate-700 bg-slate-900/40 text-center backdrop-blur-md shadow-sm">
                            <span className="text-[10px] font-bold text-slate-500 tracking-widest uppercase">Input Shape (Auto)</span>
                        </div>
                    </div>

                    {/* Layers Stack */}
                    {layers.map((layer, idx) => (
                        <div key={idx} className="flex flex-col items-center animate-in fade-in slide-in-from-bottom-4 duration-500 fill-mode-backwards" style={{ animationDelay: `${idx * 50}ms` }}>

                            {/* Connector Line Top */}
                            <div className="h-6 w-px bg-gradient-to-b from-slate-700 to-slate-600 my-1"></div>

                            {/* Layer Card */}
                            <div className="w-full bg-[#1e293b]/90 backdrop-blur-xl rounded-xl border border-slate-700/60 shadow-xl overflow-hidden group hover:border-violet-500/30 hover:shadow-2xl hover:shadow-violet-900/10 transition-all relative">
                                {/* Card Header */}
                                <div className="px-5 py-3 bg-slate-900/50 border-b border-slate-700/50 flex justify-between items-center">
                                    <div className="flex items-center gap-3">
                                        <div className="p-1.5 rounded bg-violet-500/10 text-violet-400">
                                            <Layers size={16} />
                                        </div>
                                        <div>
                                            <span className="font-bold text-slate-200 text-sm tracking-tight block">{layer.type}</span>
                                            <span className="text-[10px] text-slate-500 font-mono uppercase tracking-wider">Layer {idx + 1}</span>
                                        </div>
                                    </div>
                                    <button
                                        onClick={() => removeLayer(idx)}
                                        className="text-slate-500 hover:text-red-400 p-2 rounded-lg hover:bg-red-500/10 transition-colors opacity-0 group-hover:opacity-100"
                                        title="Remove Layer"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>

                                {/* Card Body (Config) */}
                                <div className="p-5 grid grid-cols-2 gap-x-6 gap-y-4">
                                    {/* Units */}
                                    {layer.units !== undefined && (
                                        <div>
                                            <label className="block text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-1.5">Units</label>
                                            <input
                                                type="number"
                                                className="w-full bg-[#0b1121] border border-slate-800 rounded px-3 py-2 text-sm text-slate-300 focus:border-violet-500/40 focus:outline-none transition-colors font-mono"
                                                value={layer.units}
                                                onChange={e => updateLayer(idx, 'units', parseInt(e.target.value))}
                                            />
                                        </div>
                                    )}

                                    {/* Activation */}
                                    {layer.activation !== undefined && (
                                        <div>
                                            <label className="block text-[10px] text-slate-500 uppercase font-bold tracking-wider mb-1.5">Activation</label>
                                            <div className="relative">
                                                <select
                                                    className="w-full appearance-none bg-[#0b1121] border border-slate-800 rounded px-3 py-2 text-sm text-slate-300 focus:border-violet-500/40 focus:outline-none transition-colors font-mono cursor-pointer"
                                                    value={layer.activation}
                                                    onChange={e => updateLayer(idx, 'activation', e.target.value)}
                                                >
                                                    <option value="relu">ReLU</option>
                                                    <option value="tanh">Tanh</option>
                                                    <option value="linear">Linear</option>
                                                    <option value="sigmoid">Sigmoid</option>
                                                    <option value="softmax">Softmax</option>
                                                </select>
                                                <div className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none text-slate-500">
                                                    <ArrowDown size={12} />
                                                </div>
                                            </div>
                                        </div>
                                    )}

                                    {/* LSTM: Return Seq */}
                                    {layer.return_sequences !== undefined && (
                                        <div className="col-span-2 pt-1">
                                            <label className="flex items-center gap-3 p-3 rounded-lg bg-[#0b1121] border border-slate-800 cursor-pointer hover:border-slate-600 transition-colors">
                                                <input
                                                    type="checkbox"
                                                    className="w-4 h-4 rounded bg-slate-900 border-slate-600 text-violet-500 focus:ring-0 focus:ring-offset-0"
                                                    checked={layer.return_sequences}
                                                    onChange={e => updateLayer(idx, 'return_sequences', e.target.checked)}
                                                />
                                                <span className="text-xs text-slate-300 font-medium">Return Sequences</span>
                                            </label>
                                        </div>
                                    )}

                                    {/* Dropout: Rate */}
                                    {layer.rate !== undefined && (
                                        <div className="col-span-2">
                                            <div className="flex justify-between mb-2">
                                                <label className="text-[10px] text-slate-500 uppercase font-bold tracking-wider">Dropout Rate</label>
                                                <span className="text-xs font-mono text-violet-400">{layer.rate}</span>
                                            </div>
                                            <input
                                                type="range" step="0.1" max="0.9" min="0.1"
                                                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-violet-500"
                                                value={layer.rate}
                                                onChange={e => updateLayer(idx, 'rate', parseFloat(e.target.value))}
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>
                    ))}

                    {/* Connector Line Bottom */}
                    {layers.length > 0 && <div className="h-8 w-px bg-gradient-to-b from-slate-600 to-transparent my-1 mx-auto"></div>}

                    {/* Output Placeholder */}
                    {layers.length > 0 && (
                        <div className="flex justify-center">
                            <div className="p-2 px-4 rounded-full bg-violet-500/10 text-violet-400 text-[10px] font-bold tracking-widest uppercase border border-violet-500/20 shadow-lg shadow-violet-900/10">
                                Output
                            </div>
                        </div>
                    )}

                    {layers.length === 0 && (
                        <div className="flex flex-col items-center justify-center py-32 text-slate-700">
                            <Layers size={64} className="mb-6 opacity-20" />
                            <p className="text-base font-medium">Initial Layer</p>
                            <p className="text-sm opacity-60">Add a layer to begin architecture</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ModelBuilder;
