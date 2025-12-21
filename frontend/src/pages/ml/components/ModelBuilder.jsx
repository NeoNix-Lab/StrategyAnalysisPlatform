import React from 'react';
import { Layers, Plus, Trash2, Settings } from 'lucide-react';

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
        <div className="flex gap-6 h-[500px]">
            {/* Palette */}
            <div className="w-1/4 bg-slate-800 rounded-xl p-4 border border-slate-700 flex flex-col gap-2">
                <h3 className="font-semibold text-slate-200 mb-2 flex items-center gap-2"><Plus size={16} /> Add Layer</h3>
                {LAYER_TYPES.map(lt => (
                    <button
                        key={lt.type}
                        onClick={() => addLayer(lt)}
                        className="px-4 py-3 bg-slate-900 border border-slate-700 hover:border-blue-500 rounded-lg text-left text-sm transition-colors flex justify-between group"
                    >
                        <span>{lt.type}</span>
                        <Plus size={14} className="opacity-0 group-hover:opacity-100 text-blue-500" />
                    </button>
                ))}
            </div>

            {/* Canvas / Stack */}
            <div className="flex-1 bg-slate-900/50 rounded-xl border-dashed border-2 border-slate-700 p-6 overflow-y-auto">
                <div className="flex flex-col gap-2 items-center">
                    <div className="px-4 py-2 bg-slate-800 rounded text-xs text-slate-500 border border-slate-700 w-full text-center">
                        Input Shape (Automatic)
                    </div>
                    {/* Arrow */}
                    <div className="h-4 w-0.5 bg-slate-700"></div>

                    {layers.map((layer, idx) => (
                        <div key={idx} className="w-full flex flex-col items-center">
                            <div className="w-full bg-slate-800 rounded-lg p-4 border border-slate-700 relative group hover:border-blue-500/50 transition-colors">
                                <div className="flex justify-between items-start mb-2">
                                    <span className="font-bold text-blue-400">{layer.type}</span>
                                    <button
                                        onClick={() => removeLayer(idx)}
                                        className="text-slate-600 hover:text-red-500 transition-colors"
                                    >
                                        <Trash2 size={16} />
                                    </button>
                                </div>

                                {/* Config Fields */}
                                <div className="grid grid-cols-2 gap-4">
                                    {/* Common: Units */}
                                    {layer.units !== undefined && (
                                        <div>
                                            <label className="text-[10px] uppercase text-slate-500">Units</label>
                                            <input
                                                type="number"
                                                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs"
                                                value={layer.units}
                                                onChange={e => updateLayer(idx, 'units', parseInt(e.target.value))}
                                            />
                                        </div>
                                    )}

                                    {/* Common: Activation */}
                                    {layer.activation !== undefined && (
                                        <div>
                                            <label className="text-[10px] uppercase text-slate-500">Activation</label>
                                            <select
                                                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs"
                                                value={layer.activation}
                                                onChange={e => updateLayer(idx, 'activation', e.target.value)}
                                            >
                                                <option value="relu">ReLU</option>
                                                <option value="tanh">Tanh</option>
                                                <option value="linear">Linear</option>
                                                <option value="sigmoid">Sigmoid</option>
                                                <option value="softmax">Softmax</option>
                                            </select>
                                        </div>
                                    )}

                                    {/* LSTM: Return Sequences */}
                                    {layer.return_sequences !== undefined && (
                                        <div className="flex items-center gap-2 mt-4">
                                            <input
                                                type="checkbox"
                                                checked={layer.return_sequences}
                                                onChange={e => updateLayer(idx, 'return_sequences', e.target.checked)}
                                            />
                                            <label className="text-[10px] uppercase text-slate-500">Return Seq</label>
                                        </div>
                                    )}

                                    {/* Dropout: Rate */}
                                    {layer.rate !== undefined && (
                                        <div>
                                            <label className="text-[10px] uppercase text-slate-500">Rate</label>
                                            <input
                                                type="number" step="0.1" max="1" min="0"
                                                className="w-full bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs"
                                                value={layer.rate}
                                                onChange={e => updateLayer(idx, 'rate', parseFloat(e.target.value))}
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Connector */}
                            {idx < layers.length - 1 && <div className="h-4 w-0.5 bg-slate-700 my-1"></div>}
                        </div>
                    ))}

                    {layers.length === 0 && (
                        <div className="text-slate-500 italic text-sm py-10">Add layers from the left menu</div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ModelBuilder;
