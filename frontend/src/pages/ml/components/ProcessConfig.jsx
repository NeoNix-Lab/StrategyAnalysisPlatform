import React from 'react';

const ProcessConfig = ({ config, setConfig }) => {
    const handleChange = (key, value) => {
        setConfig(prev => ({ ...prev, [key]: value }));
    };

    return (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700">
            <h3 className="font-semibold text-slate-200 mb-6">Hyperparameters</h3>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Epochs</label>
                    <input
                        type="number"
                        min="1"
                        className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                        value={config.epochs}
                        onChange={e => handleChange('epochs', parseInt(e.target.value))}
                    />
                </div>
                <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Batch Size</label>
                    <input
                        type="number"
                        min="1"
                        className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                        value={config.batch_size}
                        onChange={e => handleChange('batch_size', parseInt(e.target.value))}
                    />
                </div>

                <div className="col-span-1 md:col-span-2 grid grid-cols-2 gap-6 p-4 bg-slate-900 rounded-lg">
                    <h4 className="col-span-2 text-xs font-bold text-slate-500 uppercase">Epsilon (Exploration)</h4>

                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Start</label>
                        <input
                            type="number"
                            step="0.01"
                            min="0" max="1"
                            className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-slate-200"
                            value={config.epsilon_start}
                            onChange={e => handleChange('epsilon_start', parseFloat(e.target.value))}
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">End</label>
                        <input
                            type="number"
                            step="0.01"
                            min="0" max="1"
                            className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-slate-200"
                            value={config.epsilon_end}
                            onChange={e => handleChange('epsilon_end', parseFloat(e.target.value))}
                        />
                    </div>
                    <div>
                        <label className="block text-xs font-medium text-slate-400 mb-1">Decay</label>
                        <input
                            type="number"
                            step="0.001"
                            min="0" max="1"
                            className="w-full bg-slate-800 border border-slate-700 rounded p-2 text-slate-200"
                            value={config.epsilon_decay}
                            onChange={e => handleChange('epsilon_decay', parseFloat(e.target.value))}
                        />
                    </div>
                </div>

                <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Learning Rate</label>
                    <input
                        type="number"
                        step="0.0001"
                        className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                        value={config.learning_rate}
                        onChange={e => handleChange('learning_rate', parseFloat(e.target.value))}
                    />
                </div>
                <div>
                    <label className="block text-xs font-medium text-slate-400 mb-1">Window Size (Lookback)</label>
                    <input
                        type="number"
                        min="1"
                        className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                        value={config.window_size}
                        onChange={e => handleChange('window_size', parseInt(e.target.value))}
                    />
                </div>
            </div>
        </div>
    );
};

export default ProcessConfig;
