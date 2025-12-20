import React from 'react';
import { Plus, X, Layers } from 'lucide-react';

const LAYER_TYPES = [
    { type: 'Dense', params: { units: 64, activation: 'relu' } },
    { type: 'LSTM', params: { units: 64, return_sequences: true } },
    { type: 'Dropout', params: { rate: 0.2 } },
    { type: 'Flatten', params: {} }
];

const ModelBuilder = ({ layers, setLayers }) => {

    const addLayer = () => {
        setLayers([...layers, { ...LAYER_TYPES[0] }]);
    };

    const removeLayer = (index) => {
        setLayers(layers.filter((_, i) => i !== index));
    };

    const updateLayerType = (index, newType) => {
        const template = LAYER_TYPES.find(l => l.type === newType);
        const newLayers = [...layers];
        newLayers[index] = { ...template };
        setLayers(newLayers);
    };

    const updateLayerParam = (index, param, value) => {
        const newLayers = [...layers];
        newLayers[index] = {
            ...newLayers[index],
            params: { ...newLayers[index].params, [param]: value }
        };
        setLayers(newLayers);
    };

    return (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 h-full flex flex-col">
            <h2 className="text-xl font-semibold mb-4 flex items-center gap-2">
                <Layers size={20} className="text-purple-400" /> Model Architecture
            </h2>

            <div className="flex-1 overflow-y-auto space-y-3 pr-2">
                {/* Input Layer (Always present visually) */}
                <div className="p-3 bg-slate-900/50 rounded border border-slate-700 border-dashed opacity-75">
                    <div className="text-sm font-medium text-slate-400">Input Layer</div>
                    <div className="text-xs text-slate-500 mt-1">Shape: (Window Size, Features)</div>
                </div>

                {layers.map((layer, index) => (
                    <div key={index} className="p-3 bg-slate-900 rounded border border-slate-600 relative group">
                        <button
                            onClick={() => removeLayer(index)}
                            className="absolute top-2 right-2 text-slate-500 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                        >
                            <X size={16} />
                        </button>

                        <div className="flex gap-3 mb-3">
                            <div className="flex-1">
                                <label className="block text-xs text-slate-500 mb-1">Layer Type</label>
                                <select
                                    className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200"
                                    value={layer.type}
                                    onChange={(e) => updateLayerType(index, e.target.value)}
                                >
                                    {LAYER_TYPES.map(t => <option key={t.type} value={t.type}>{t.type}</option>)}
                                </select>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-3">
                            {Object.keys(layer.params).map(param => (
                                <div key={param}>
                                    <label className="block text-xs text-slate-500 mb-1 capitalize">{param.replace('_', ' ')}</label>
                                    <input
                                        type={typeof layer.params[param] === 'number' ? 'number' : 'text'}
                                        className="w-full bg-slate-800 border border-slate-700 rounded px-2 py-1 text-sm text-slate-200"
                                        value={layer.params[param]}
                                        onChange={(e) => updateLayerParam(index, param, e.target.type === 'number' ? parseFloat(e.target.value) : e.target.value)}
                                    />
                                </div>
                            ))}
                        </div>
                    </div>
                ))}

                {/* Output Layer (Always present visually) */}
                <div className="p-3 bg-slate-900/50 rounded border border-slate-700 border-dashed opacity-75">
                    <div className="text-sm font-medium text-slate-400">Output Layer</div>
                    <div className="text-xs text-slate-500 mt-1">Actions (Dense 3)</div>
                </div>
            </div>

            <button
                onClick={addLayer}
                className="mt-4 w-full py-2 border border-dashed border-slate-600 rounded text-slate-400 hover:bg-slate-700/50 hover:text-slate-200 transition-colors flex items-center justify-center gap-2"
            >
                <Plus size={16} /> Add Layer
            </button>
        </div>
    );
};

export default ModelBuilder;
