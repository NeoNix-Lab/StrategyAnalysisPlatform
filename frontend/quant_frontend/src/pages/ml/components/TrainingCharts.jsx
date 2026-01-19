import React, { useMemo } from 'react';
import {
    LineChart, Line, AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts';
import { Activity, TrendingUp, Zap, Clock, TrendingDown } from 'lucide-react';

const ChartCard = ({ title, icon: Icon, children, color }) => (
    <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-4 flex flex-col h-[300px] shadow-sm hover:shadow-md transition-shadow duration-300">
        <div className="flex items-center gap-2 mb-4">
            <div className={`p-1.5 rounded-lg bg-${color}-500/10 border border-${color}-500/20`}>
                <Icon size={14} className={`text-${color}-400`} />
            </div>
            <h3 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">{title}</h3>
        </div>
        <div className="flex-1 w-full min-h-0">
            {children}
        </div>
    </div>
);

const CustomTooltip = ({ active, payload, label, color }) => {
    if (active && payload && payload.length) {
        return (
            <div className="bg-slate-900/90 border border-slate-700 p-2 rounded-lg shadow-xl text-xs backdrop-blur-md z-50">
                <p className="text-slate-400 font-mono mb-1">{label}</p>
                {payload.map((p, i) => (
                    <p key={i} className="font-semibold" style={{ color: p.color || color }}>
                        {p.name}: {typeof p.value === 'number' ? p.value.toLocaleString(undefined, { maximumFractionDigits: 4 }) : p.value}
                    </p>
                ))}
            </div>
        );
    }
    return null;
};

const TrainingCharts = ({ data, equityData }) => {

    // Process Data for Charts
    const processedData = useMemo(() => {
        if (!data || data.length === 0) return [];
        return data.map(d => ({
            ...d,
            epochLabel: `Ep ${d.epoch}`,
            // Ensure numeric values
            reward: Number(d.reward || 0),
            loss: Number(d.loss || 0),
            epsilon: Number(d.epsilon || 0),
            length: Number(d.length || 0),
        }));
    }, [data]);

    // Process Equity Data
    const processedEquity = useMemo(() => {
        if (equityData && equityData.length > 0) {
            return equityData.map(d => ({
                time: new Date(d.time || Date.now()).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                fullTime: new Date(d.time || Date.now()).toLocaleString(),
                pnl: Number(d.pnl || d.balance || 0),
                drawdown: Number(d.drawdown || 0)
            }));
        }
        // Fallback to history balance if available
        if (processedData.length > 0 && processedData[0].balance !== undefined) {
            return processedData.map(d => ({
                time: `Ep ${d.epoch}`,
                fullTime: `Episode ${d.epoch}`,
                pnl: Number(d.balance),
                drawdown: 0
            }));
        }
        return [];
    }, [equityData, processedData]);

    if (processedData.length === 0 && processedEquity.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-20 bg-slate-800/20 rounded-xl border border-dashed border-slate-700">
                <Activity className="text-slate-600 mb-2" size={32} />
                <span className="text-slate-500 text-sm">Waiting for training metrics...</span>
            </div>
        );
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">

            {/* Top Grid: Core RL Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 xl:grid-cols-2 gap-4">

                {/* 1. AVG REWARD */}
                <ChartCard title="Average Reward" icon={TrendingUp} color="emerald">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={processedData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorReward" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                            <XAxis dataKey="epoch" stroke="#475569" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                            <YAxis stroke="#475569" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} domain={['auto', 'auto']} />
                            <Tooltip content={<CustomTooltip color="#10b981" />} />
                            <Area
                                type="monotone"
                                dataKey="reward"
                                stroke="#10b981"
                                strokeWidth={2}
                                fillOpacity={1}
                                fill="url(#colorReward)"
                                animationDuration={500}
                                isAnimationActive={false} // Dissable for live peformance
                            />
                        </AreaChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* 2. LOSS */}
                <ChartCard title="Training Loss" icon={TrendingDown} color="rose">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={processedData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                            <XAxis dataKey="epoch" stroke="#475569" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                            <YAxis stroke="#475569" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                            <Tooltip content={<CustomTooltip color="#f43f5e" />} />
                            <Line
                                type="monotone"
                                dataKey="loss"
                                stroke="#f43f5e"
                                strokeWidth={2}
                                dot={false}
                                activeDot={{ r: 4, strokeWidth: 0 }}
                                isAnimationActive={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* 3. EPSILON */}
                <ChartCard title="Epsilon (Exploration)" icon={Zap} color="amber">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={processedData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                            <XAxis dataKey="epoch" stroke="#475569" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                            <YAxis stroke="#475569" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} domain={[0, 1]} />
                            <Tooltip content={<CustomTooltip color="#fbbf24" />} />
                            <Line
                                type="stepAfter"
                                dataKey="epsilon"
                                stroke="#fbbf24"
                                strokeWidth={2}
                                dot={false}
                                isAnimationActive={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </ChartCard>

                {/* 4. EPISODE LENGTH */}
                <ChartCard title="Episode Length (Steps)" icon={Clock} color="blue">
                    <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={processedData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                            <XAxis dataKey="epoch" stroke="#475569" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                            <YAxis stroke="#475569" tick={{ fontSize: 10 }} tickLine={false} axisLine={false} />
                            <Tooltip content={<CustomTooltip color="#3b82f6" />} />
                            <Line
                                type="monotone"
                                dataKey="length"
                                stroke="#3b82f6"
                                strokeWidth={2}
                                dot={false}
                                strokeOpacity={0.8}
                                isAnimationActive={false}
                            />
                        </LineChart>
                    </ResponsiveContainer>
                </ChartCard>
            </div>

            {/* Bottom: Equity Curve (Full Width) */}
            <div className="bg-slate-900/50 backdrop-blur-sm border border-slate-700/50 rounded-xl p-5 shadow-sm">
                <div className="flex items-center justify-between mb-4">
                    <div className="flex items-center gap-2">
                        <div className="p-1.5 rounded-lg bg-indigo-500/10 border border-indigo-500/20">
                            <Activity size={16} className="text-indigo-400" />
                        </div>
                        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Equity Curve (PnL)</h3>
                    </div>
                    {processedEquity.length > 0 && (
                        <div className="flex items-center gap-4 text-xs font-mono">
                            <span className={processedEquity[processedEquity.length - 1].pnl >= 0 ? "text-green-400" : "text-red-400"}>
                                PnL: {processedEquity[processedEquity.length - 1].pnl.toFixed(2)}
                            </span>
                            <span className="text-slate-500">
                                Trades: {processedEquity.length}
                            </span>
                        </div>
                    )}
                </div>

                <div className="h-[300px] w-full">
                    {processedEquity.length > 0 ? (
                        <ResponsiveContainer width="100%" height="100%">
                            <AreaChart data={processedEquity} margin={{ top: 5, right: 30, left: 0, bottom: 0 }}>
                                <defs>
                                    <linearGradient id="colorPnL" x1="0" y1="0" x2="0" y2="1">
                                        <stop offset="5%" stopColor="#6366f1" stopOpacity={0.3} />
                                        <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
                                    </linearGradient>
                                </defs>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                                <XAxis
                                    dataKey="time"
                                    stroke="#475569"
                                    tick={{ fontSize: 10 }}
                                    tickLine={false}
                                    axisLine={false}
                                    minTickGap={30}
                                />
                                <YAxis
                                    stroke="#475569"
                                    tick={{ fontSize: 10 }}
                                    tickLine={false}
                                    axisLine={false}
                                />
                                <Tooltip content={<CustomTooltip color="#6366f1" />} />
                                <Area
                                    type="monotone"
                                    dataKey="pnl"
                                    name="Balance"
                                    stroke="#6366f1"
                                    strokeWidth={3}
                                    fillOpacity={1}
                                    fill="url(#colorPnL)"
                                    isAnimationActive={false}
                                />
                            </AreaChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-slate-600">
                            <Clock size={24} className="mb-2 opacity-50" />
                            <span className="text-xs">Waiting for equity data...</span>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TrainingCharts;
