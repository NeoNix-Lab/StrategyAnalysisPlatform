import React from 'react';
import { Sliders } from 'lucide-react';

const Hyperparameters = ({ config, setConfig }) => {

    const handleChange = (key, value) => {
        setConfig(prev => ({
            ...prev,
            [key]: parseFloat(value) || value // Basic handling, improve if needed
        }));
    };

    return (
        <div className="bg-slate-800 rounded-xl p-6 border border-slate-700 h-full">
            <h2 className="text-xl font-semibold mb-6 flex items-center gap-2">
                <Sliders size={20} className="text-green-400" /> Hyperparameters
            </h2>

            <div className="space-y-6">

                {/* Training Config */}
                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Training Loop</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Epochs</label>
                            <input
                                type="number"
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                                value={config.epochs}
                                onChange={(e) => handleChange('epochs', e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Batch Size</label>
                            <input
                                type="number"
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                                value={config.batch_size}
                                onChange={(e) => handleChange('batch_size', e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Learning Rate</label>
                            <input
                                type="number"
                                step="0.0001"
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                                value={config.learning_rate}
                                onChange={(e) => handleChange('learning_rate', e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Window Size</label>
                            <input
                                type="number"
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                                value={config.window_size}
                                onChange={(e) => handleChange('window_size', e.target.value)}
                            />
                        </div>
                    </div>
                </div>

                <div className="border-t border-slate-700 my-4"></div>

                {/* RL specific */}
                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wider">Reinforcement Learning</h3>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Gamma (Discount)</label>
                            <input
                                type="number"
                                step="0.01" max="1"
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                                value={config.gamma}
                                onChange={(e) => handleChange('gamma', e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Tau (Soft Update)</label>
                            <input
                                type="number"
                                step="0.001"
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                                value={config.tau}
                                onChange={(e) => handleChange('tau', e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Epsilon Start</label>
                            <input
                                type="number"
                                step="0.1" max="1"
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                                value={config.epsilon_start}
                                onChange={(e) => handleChange('epsilon_start', e.target.value)}
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-slate-400 mb-1">Epsilon End</label>
                            <input
                                type="number"
                                step="0.01"
                                className="w-full bg-slate-900 border border-slate-700 rounded p-2 text-slate-200"
                                value={config.epsilon_end}
                                onChange={(e) => handleChange('epsilon_end', e.target.value)}
                            />
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};

export default Hyperparameters;
