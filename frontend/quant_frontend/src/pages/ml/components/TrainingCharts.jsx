import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

// Helper for robust sizing
const AutoResponsive = ({ children, className }) => {
    const containerRef = React.useRef(null);
    const [size, setSize] = React.useState({ width: 0, height: 0 });

    React.useEffect(() => {
        if (!containerRef.current) return;
        const resizeObserver = new ResizeObserver((entries) => {
            if (!entries || entries.length === 0) return;
            // Use contentRect for precise inner dimensions
            const { width, height } = entries[0].contentRect;
            setSize({ width, height });
        });
        resizeObserver.observe(containerRef.current);
        return () => resizeObserver.disconnect();
    }, []);

    return (
        <div ref={containerRef} className={className} style={{ width: '100%', height: '100%', overflow: 'hidden' }}>
            {size.width > 0 && size.height > 0 ? (
                React.cloneElement(children, { width: size.width, height: size.height })
            ) : (
                <div className="flex items-center justify-center h-full text-slate-700 text-[10px]">Initializing Chart...</div>
            )}
        </div>
    );
};

const TrainingCharts = ({ data, equityData }) => {
    // Normalization Logic for Equity Curve
    // If we receive RL history (epoch/balance), map it to the expected structure (time/pnl).
    const finalEquityData = React.useMemo(() => {
        // Prioritize specific equity data (from metrics endpoint)
        if (equityData && equityData.length > 0) {
            // Case 1: Standard Analyzer Format (has 'pnl')
            if (equityData[0].pnl !== undefined) return equityData;

            // Case 2: Maybe it's raw history passed as equityData?
            return equityData.map(d => ({
                time: `Epoch ${d.epoch}`,
                pnl: d.balance !== undefined ? d.balance : d.reward,
                drawdown: 0
            }));
        }

        // Fallback: Use Training History (data prop)
        if (data && data.length > 0) {
            return data.map(d => ({
                time: `Epoch ${d.epoch}`,
                pnl: d.balance !== undefined ? d.balance : d.reward, // Use balance (total_reward) as PnL proxy
                drawdown: 0
            }));
        }

        return [];
    }, [data, equityData]);

    const hasHistory = data && data.length > 0;
    const hasEquity = finalEquityData && finalEquityData.length > 0;

    if (!hasHistory && !hasEquity) return <div className="text-slate-500 text-xs italic text-center p-4">No metrics available yet.</div>;

    return (
        <div className="flex flex-col gap-4 mb-4">
            {/* DEBUG OVERLAY - REMOVE LATER */}
            {/* <div className="text-[10px] text-yellow-500 font-mono bg-black/50 p-2 break-all">
                DEBUG: History Len: {data?.length}. First: {JSON.stringify(data?.[0])}
            </div> */}

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Reward Chart */}
                <div className="bg-[#0f172a] p-4 rounded-lg border border-slate-700 h-[250px] relative">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 z-10 relative">Avg Reward per Epoch</h3>
                    <div className="absolute inset-x-0 bottom-0 top-8 px-2 pb-2 overflow-hidden flex justify-center">
                        {hasHistory ? (
                            <LineChart width={350} height={200} data={data} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                <XAxis dataKey="epoch" stroke="#64748b" tick={{ fontSize: 10 }} />
                                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} domain={['auto', 'auto']} />
                                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#e2e8f0' }} itemStyle={{ fontSize: 12 }} />
                                <Line type="linear" dataKey="reward" stroke="#10b981" strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 4 }} isAnimationActive={false} />
                            </LineChart>
                        ) : (
                            <div className="flex h-full items-center justify-center text-slate-600 text-xs">Waiting for data...</div>
                        )}
                    </div>
                </div>

                {/* Loss Chart */}
                <div className="bg-[#0f172a] p-4 rounded-lg border border-slate-700 h-[250px] relative">
                    <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 z-10 relative">Training Loss</h3>
                    <div className="absolute inset-x-0 bottom-0 top-8 px-2 pb-2 flex justify-center">
                        {hasHistory ? (
                            <LineChart width={350} height={200} data={data} margin={{ top: 5, right: 10, bottom: 5, left: -20 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                                <XAxis dataKey="epoch" stroke="#64748b" tick={{ fontSize: 10 }} />
                                <YAxis stroke="#64748b" tick={{ fontSize: 10 }} domain={['auto', 'auto']} />
                                <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#e2e8f0' }} itemStyle={{ fontSize: 12 }} />
                                <Line type="linear" dataKey="loss" stroke="#ef4444" strokeWidth={2} dot={{ r: 2 }} activeDot={{ r: 4 }} isAnimationActive={false} />
                            </LineChart>
                        ) : (
                            <div className="flex h-full items-center justify-center text-slate-600 text-xs">Waiting for data...</div>
                        )}
                    </div>
                </div>
            </div>

            {/* Equity Curve (New) */}
            <div className="bg-[#0f172a] p-4 rounded-lg border border-slate-700 h-[300px] relative">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-2 z-10 relative">
                    <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                    Equity Curve (PnL)
                </h3>
                <div className="absolute inset-x-0 bottom-0 top-8 px-2 pb-2 flex justify-center">
                    {hasEquity ? (
                        <LineChart width={700} height={250} data={finalEquityData} margin={{ top: 5, right: 30, bottom: 5, left: -10 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            {finalEquityData[0]?.time?.toString().includes("Epoch") ? (
                                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} />
                            ) : (
                                <XAxis dataKey="time" stroke="#64748b" tick={{ fontSize: 10 }} tickFormatter={(val) => new Date(val).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} />
                            )}
                            <YAxis stroke="#64748b" tick={{ fontSize: 10 }} />
                            <Tooltip contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#e2e8f0' }} itemStyle={{ fontSize: 12 }} labelFormatter={(label) => label} />
                            <Legend wrapperStyle={{ fontSize: '10px' }} />
                            <Line type="monotone" dataKey="pnl" name="Total PnL" stroke="#3b82f6" strokeWidth={2} dot={false} />
                            {/* Only show drawdown if it exists and is non-zero */}
                            <Line type="monotone" dataKey="drawdown" name="Drawdown" stroke="#f43f5e" strokeWidth={1} dot={false} strokeOpacity={0.5} />
                        </LineChart>
                    ) : (
                        <div className="flex h-full items-center justify-center text-slate-600 text-xs text-center p-4">
                            Waiting for trades...<br />(Equity curve is generated after first closed trade)
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default TrainingCharts;
