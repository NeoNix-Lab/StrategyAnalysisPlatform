import React, { useMemo, useState } from 'react';
import { Database, Brain, Settings, Activity, Zap, Server, ChevronDown, ChevronRight, Maximize2, Minimize2 } from 'lucide-react';

const CollapsibleSection = ({ title, icon: Icon, children, color, defaultOpen = false, forcedState = null }) => {
    const [isOpenInternal, setIsOpenInternal] = useState(defaultOpen);

    const isOpen = forcedState !== null ? forcedState : isOpenInternal;
    const toggle = () => setIsOpenInternal(!isOpenInternal);

    return (
        <div className="border border-slate-700/50 rounded-xl overflow-hidden bg-slate-900/40 backdrop-blur-sm mb-3 transition-colors duration-300 hover:border-slate-600/50 shadow-sm">
            <button
                onClick={toggle}
                className="w-full flex items-center justify-between p-4 bg-white/5 hover:bg-white/10 transition-colors"
            >
                <div className="flex items-center gap-3">
                    <div className={`p-1.5 rounded-lg bg-${color}-500/10 border border-${color}-500/20`}>
                        <Icon size={16} className={`text-${color}-400`} />
                    </div>
                    <span className="text-sm font-semibold text-slate-200 tracking-wide uppercase">{title}</span>
                </div>
                {isOpen ? <ChevronDown size={16} className="text-slate-400" /> : <ChevronRight size={16} className="text-slate-500" />}
            </button>

            <div
                className={`transition-all duration-300 ease-in-out overflow-hidden ${isOpen ? 'max-h-[500px] opacity-100' : 'max-h-0 opacity-0'
                    }`}
            >
                <div className="p-5 border-t border-slate-700/50">
                    {children}
                </div>
            </div>
        </div>
    );
};

const ValueRow = ({ label, value, sub, large = false }) => (
    <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center py-2 border-b border-slate-800/50 last:border-0 hover:bg-white/5 px-2 rounded-lg transition-colors group">
        <span className="text-xs uppercase font-semibold text-slate-500 group-hover:text-slate-400 transition-colors mb-1 sm:mb-0">{label}</span>
        <div className="text-right">
            <div className={`font-mono text-slate-200 ${large ? 'text-lg' : 'text-sm'} break-all`}>
                {value !== undefined && value !== null ? value.toString() : <span className="text-slate-600">-</span>}
            </div>
            {sub && <div className="text-[10px] text-slate-500 font-medium mt-0.5">{sub}</div>}
        </div>
    </div>
);

const RunConfiguration = ({ logs = [] }) => {

    // Parse logs into structured data
    const config = useMemo(() => {
        const data = {
            dataset: {},
            model: {},
            trainer: {},
            optimization: {},
            replay: {},
            status: 'Pending Logs...'
        };

        if (!logs || logs.length === 0) return data;

        const parseKV = (str) => {
            const result = {};
            const parts = str.split(' | ')[1] || str;
            const regex = /(\w+)=([^\s=\[\]]+|\[.*?\]|'[^']*'|"[^"]*")/g;
            let match;
            while ((match = regex.exec(parts)) !== null) {
                let val = match[2];
                if (val.startsWith("'") && val.endsWith("'")) val = val.slice(1, -1);
                if (val === 'None') val = null;
                if (val === 'True') val = true;
                if (val === 'False') val = false;
                result[match[1]] = val;
            }
            return result;
        };

        logs.forEach(log => {
            if (log.includes("Dataset loaded |")) {
                data.dataset = parseKV(log);
            }
            else if (log.includes("Model config |")) {
                data.model = parseKV(log);
            }
            else if (log.includes("Training init |")) {
                const params = parseKV(log);
                data.trainer = {
                    episodes: params.episodes,
                    batch_size: params.batch_size,
                    dataset_len: params.dataset_len,
                    initial_balance: params.initial_balance,
                    gamma: params.gamma,
                    tau: params.tau
                };
                data.optimization = {
                    optimizer: params.optimizer,
                    loss: params.loss,
                    decay_mode: params.decay_mode,
                    decay_rate: params.decay_rate,
                    decay_steps: params.decay_steps,
                    decay_frequency: params.decay_frequency,
                    epsilon_start: params.epsilon_start,
                    epsilon_end: params.epsilon_end
                };
                data.replay = {
                    capacity: params.replay_capacity,
                    log_every: params.log_every_steps
                };
            }
        });

        if (Object.keys(data.dataset).length > 0) data.status = 'Loaded';
        return data;

    }, [logs]);

    const [globalExpand, setGlobalExpand] = useState(null); // true = all open, false = all closed, null = individual

    if (logs.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-64 text-slate-500 bg-slate-900/30 rounded-xl border border-slate-800/50">
                <div className="bg-slate-800 p-4 rounded-full mb-3 shadow-inner">
                    <Activity size={32} className="opacity-40" />
                </div>
                <p className="text-sm font-mono tracking-wide">Waiting for logs to extract configuration...</p>
            </div>
        );
    }

    return (
        <div className="max-w-4xl mx-auto space-y-4 animate-in fade-in slide-in-from-bottom-2 duration-500">

            <div className="flex justify-end gap-2 mb-2">
                <button
                    onClick={() => setGlobalExpand(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors border border-slate-700"
                >
                    <Maximize2 size={12} /> Expand All
                </button>
                <button
                    onClick={() => setGlobalExpand(false)}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors border border-slate-700"
                >
                    <Minimize2 size={12} /> Collapse All
                </button>
            </div>

            <CollapsibleSection title="Data Environment" icon={Database} color="blue" defaultOpen={true} forcedState={globalExpand}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2">
                    <ValueRow label="Total Records" value={config.dataset.records} large />
                    <ValueRow label="Initial Balance" value={config.trainer.initial_balance} sub="Starting Capital" />
                    <ValueRow label="Features" value={config.dataset.columns || config.trainer.features} />
                    <ValueRow label="Lookback Window" value={config.model.window} />
                    <ValueRow label="Data Split" value={config.model.split} />
                </div>
            </CollapsibleSection>

            <CollapsibleSection title="Model Architecture" icon={Brain} color="purple" defaultOpen={true} forcedState={globalExpand}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2">
                    <ValueRow label="Hidden Layers" value={config.model.layers} large />
                    <ValueRow label="Action Space" value={config.model.actions} large />
                    <div className="col-span-2 mt-2 pt-2 border-t border-slate-800/50">
                        <ValueRow label="Status Labels" value={config.model.status} />
                    </div>
                </div>
            </CollapsibleSection>

            <CollapsibleSection title="Optimization Strategy" icon={Zap} color="amber" forcedState={globalExpand}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2">
                    <ValueRow label="Optimizer" value={config.optimization.optimizer} large />
                    <ValueRow label="Loss Function" value={config.optimization.loss} large />

                    <div className="col-span-1 md:col-span-2 my-2 p-3 bg-slate-800/50 rounded-lg border border-slate-700/50">
                        <div className="flex justify-between items-center text-xs text-slate-500 mb-2 uppercase font-semibold">
                            <span>Epsilon Schedule</span>
                            <span className="flex items-center gap-2">
                                <span className="text-slate-400">{config.optimization.decay_frequency === 'episode' ? 'Per Episode' : 'Per Step'}</span>
                                <span className="px-1.5 py-0.5 rounded bg-slate-700 text-slate-300 border border-slate-600 font-mono text-[10px]">{config.optimization.decay_mode}</span>
                            </span>
                        </div>
                        <div className="flex items-center justify-between font-mono text-lg text-amber-400">
                            <span>{config.optimization.epsilon_start}</span>
                            <span className="text-slate-600 text-sm">➜</span>
                            <span>{config.optimization.epsilon_end}</span>
                        </div>
                        <div className="text-center text-xs text-slate-500 mt-1">
                            Decay Rate: {config.optimization.decay_rate || 'N/A'} (over {config.optimization.decay_steps} steps)
                        </div>
                    </div>
                </div>
            </CollapsibleSection>

            <CollapsibleSection title="Training Loop" icon={Activity} color="emerald" forcedState={globalExpand}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2">
                    <ValueRow label="Total Episodes" value={config.trainer.episodes} large />
                    <ValueRow label="Batch Size" value={config.trainer.batch_size} />
                    <ValueRow label="Gamma (Discournt)" value={config.trainer.gamma} />
                    <ValueRow label="Tau (Soft Update)" value={config.trainer.tau} />
                </div>
            </CollapsibleSection>

            <CollapsibleSection title="System & Replay" icon={Server} color="slate" forcedState={globalExpand}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-2">
                    <ValueRow label="Replay Buffer Capacity" value={config.replay.capacity} />
                    <ValueRow label="Logging Interval" value={config.replay.log_every} sub="steps" />
                </div>
            </CollapsibleSection>

        </div>
    );
};

export default RunConfiguration;
