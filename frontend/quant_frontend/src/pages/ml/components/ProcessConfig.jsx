import React from 'react';
import { Settings, Zap, Clock, Activity } from 'lucide-react';

const ProcessConfig = ({ config, setConfig }) => {
    const handleChange = (key, value) => {
        setConfig(prev => ({ ...prev, [key]: value }));
    };

    const InputGroup = ({ label, value, onChange, type = "number", step = "1", min, max }) => (
        <div className="flex flex-col gap-2">
            <label className="text-[11px] uppercase font-bold text-slate-500 tracking-wider">{label}</label>
            <input
                type={type}
                step={step}
                min={min}
                max={max}
                className="w-full bg-[#0b1121] border border-slate-800 rounded px-4 py-3 text-sm text-slate-300 focus:border-blue-500/50 focus:bg-slate-900 focus:outline-none transition-all font-mono"
                value={value}
                onChange={onChange}
            />
        </div>
    );

    const SectionHeader = ({ icon: Icon, title, colorClass, bgClass }) => (
        <div className="flex items-center gap-3 mb-6 pb-4 border-b border-slate-800/50">
            <div className={`p-2 rounded-lg ${bgClass}`}>
                <Icon size={20} className={colorClass} />
            </div>
            <h3 className="text-base font-semibold text-slate-200 tracking-tight">{title}</h3>
        </div>
    );

    const SelectGroup = ({ label, value, onChange, options }) => (
        <div className="flex flex-col gap-2">
            <label className="text-[11px] uppercase font-bold text-slate-500 tracking-wider">{label}</label>
            <select
                className="w-full bg-[#0b1121] border border-slate-800 rounded px-4 py-3 text-sm text-slate-300 focus:border-blue-500/50 focus:bg-slate-900 focus:outline-none transition-all font-mono appearance-none"
                value={value || ""}
                onChange={onChange}
            >
                {options.map(opt => (
                    <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
            </select>
        </div>
    );

    return (
        <div className="grid grid-cols-1 gap-8 max-w-4xl mx-auto py-4">

            {/* General Settings */}
            <div className="bg-[#1e293b]/40 rounded-xl border border-slate-700/50 p-6 backdrop-blur-sm">
                <SectionHeader
                    icon={Clock}
                    title="Training Dynamics"
                    colorClass="text-blue-400"
                    bgClass="bg-blue-500/10"
                />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <InputGroup
                        label="Epochs"
                        value={config.epochs}
                        onChange={e => handleChange('epochs', parseInt(e.target.value))}
                        min="1"
                    />
                    <InputGroup
                        label="Batch Size"
                        value={config.batch_size}
                        onChange={e => handleChange('batch_size', parseInt(e.target.value))}
                        min="1"
                    />
                    <InputGroup
                        label="Window Size (Lookback)"
                        value={config.window_size}
                        onChange={e => handleChange('window_size', parseInt(e.target.value))}
                        min="1"
                    />
                    <InputGroup
                        label="Fees (Per Trade)"
                        value={config.fees}
                        onChange={e => handleChange('fees', parseFloat(e.target.value))}
                        step="0.0001"
                        min="0"
                    />
                </div>
            </div>

            {/* Optimization */}
            <div className="bg-[#1e293b]/40 rounded-xl border border-slate-700/50 p-6 backdrop-blur-sm">
                <SectionHeader
                    icon={Settings}
                    title="Optimization"
                    colorClass="text-purple-400"
                    bgClass="bg-purple-500/10"
                />
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                    <InputGroup
                        label="Learning Rate"
                        value={config.learning_rate}
                        onChange={e => handleChange('learning_rate', parseFloat(e.target.value))}
                        step="0.0001"
                    />
                    <SelectGroup
                        label="Optimizer"
                        value={config.optimizer || "Adam"}
                        onChange={e => handleChange('optimizer', e.target.value)}
                        options={[
                            { label: "Adam", value: "Adam" },
                            { label: "SGD", value: "SGD" },
                            { label: "RMSprop", value: "RMSprop" },
                            { label: "Adagrad", value: "Adagrad" },
                            { label: "Nadam", value: "Nadam" },
                            { label: "Adamax", value: "Adamax" }
                        ]}
                    />
                    <SelectGroup
                        label="Loss Function"
                        value={config.loss || "huber"}
                        onChange={e => handleChange('loss', e.target.value)}
                        options={[
                            { label: "Huber", value: "huber" },
                            { label: "Mean Squared Error", value: "mean_squared_error" },
                            { label: "Mean Absolute Error", value: "mean_absolute_error" },
                            { label: "Binary Crossentropy", value: "binary_crossentropy" },
                            { label: "Categorical Crossentropy", value: "categorical_crossentropy" },
                            { label: "Kullback Leibler", value: "kullback_leibler_divergence" }
                        ]}
                    />
                </div>
            </div>

            {/* Exploration (Epsilon) */}
            <div className="bg-[#1e293b]/40 rounded-xl border border-slate-700/50 p-6 backdrop-blur-sm">
                <SectionHeader
                    icon={Zap}
                    title="Exploration (Epsilon Greedy)"
                    colorClass="text-yellow-400"
                    bgClass="bg-yellow-500/10"
                />

                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 bg-[#0b1121]/50 p-6 rounded-xl border border-slate-800/50">
                    <InputGroup
                        label="Start Value"
                        value={config.epsilon_start}
                        onChange={e => handleChange('epsilon_start', parseFloat(e.target.value))}
                        step="0.01" min="0" max="1"
                    />
                    <InputGroup
                        label="End Value"
                        value={config.epsilon_end}
                        onChange={e => handleChange('epsilon_end', parseFloat(e.target.value))}
                        step="0.01" min="0" max="1"
                    />
                    <InputGroup
                        label="Decay Rate"
                        value={config.epsilon_decay}
                        onChange={e => handleChange('epsilon_decay', parseFloat(e.target.value))}
                        step="0.001" min="0" max="1"
                    />
                </div>
                <div className="mt-4 flex items-center gap-2 text-xs text-slate-500 px-2">
                    <Activity size={14} />
                    <span>
                        Decay traverses from <span className="text-slate-300 font-mono">{config.epsilon_start}</span> to <span className="text-slate-300 font-mono">{config.epsilon_end}</span>.
                    </span>
                </div>
            </div>
        </div>
    );
};

export default ProcessConfig;
