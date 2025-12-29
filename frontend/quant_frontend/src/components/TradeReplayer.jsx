import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { Play, Pause, FastForward, SkipBack, X } from 'lucide-react';

// Attempt to use relative path if proxied, else localhost
const API_BASE = 'http://localhost:8000';

export const TradeReplayer = ({ tradeId, onClose }) => {
    const [trade, setTrade] = useState(null);
    const [allBars, setAllBars] = useState([]);
    const [displayedBars, setDisplayedBars] = useState([]);
    const [isPlaying, setIsPlaying] = useState(false);
    const [speed, setSpeed] = useState(1);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [loading, setLoading] = useState(true);
    const [timeframe, setTimeframe] = useState('1m'); // Default

    const chartContainerRef = useRef();
    const chartRef = useRef();
    const seriesRef = useRef();
    const timerRef = useRef();

    // 1. Fetch Trade Details
    useEffect(() => {
        const fetchTrade = async () => {
            try {
                const res = await fetch(`${API_BASE}/api/trades/${tradeId}`);
                if (!res.ok) throw new Error('Failed to fetch trade');
                const data = await res.json();
                setTrade(data);
                if (data.timeframe) {
                    setTimeframe(data.timeframe);
                }
            } catch (err) {
                console.error(err);
            }
        };
        if (tradeId) fetchTrade();
    }, [tradeId]);

    // 2. Fetch Bars when Trade is loaded
    useEffect(() => {
        if (!trade) return;

        const fetchBars = async () => {
            setLoading(true);
            try {
                // Buffer: 2 hours before, 2 hours after
                const entryTime = new Date(trade.entry_time);
                const exitTime = new Date(trade.exit_time);

                const start = new Date(entryTime.getTime() - 2 * 60 * 60 * 1000).toISOString();
                const end = new Date(exitTime.getTime() + 2 * 60 * 60 * 1000).toISOString();

                const url = `${API_BASE}/api/bars/?run_id=${trade.run_id}&symbol=${trade.symbol}&timeframe=${timeframe}&start_utc=${start}&end_utc=${end}`;
                const res = await fetch(url);
                const data = await res.json();

                // Sort
                const sorted = data.sort((a, b) => new Date(a.ts_utc) - new Date(b.ts_utc));

                // Format
                const formatted = sorted.map(b => ({
                    time: new Date(b.ts_utc).getTime() / 1000,
                    open: b.open,
                    high: b.high,
                    low: b.low,
                    close: b.close
                }));

                setAllBars(formatted);

                // Initial Position: 20 bars before entry
                const entryTs = entryTime.getTime() / 1000;
                const entryIndex = formatted.findIndex(b => b.time >= entryTs);
                const startIndex = Math.max(0, entryIndex - 30);

                setCurrentIndex(startIndex);
                setDisplayedBars(formatted.slice(0, startIndex + 1));
                setLoading(false);

            } catch (err) {
                console.error(err);
                setLoading(false);
            }
        };

        fetchBars();
    }, [trade, timeframe]);

    // 3. Initialize Chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: { background: { type: ColorType.Solid, color: '#0f172a' }, textColor: '#94a3b8' },
            grid: { vertLines: { color: '#1e293b' }, horzLines: { color: '#1e293b' } },
            timeScale: { timeVisible: true, secondsVisible: false, borderColor: '#334155' },
            rightPriceScale: { borderColor: '#334155' },
            crosshair: {
                vertLine: { labelBackgroundColor: '#334155' },
                horzLine: { labelBackgroundColor: '#334155' },
            },
        });

        const series = chart.addCandlestickSeries({
            upColor: '#4ade80', downColor: '#f87171',
            borderVisible: false, wickUpColor: '#4ade80', wickDownColor: '#f87171'
        });

        chartRef.current = chart;
        seriesRef.current = series;

        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({ width: chartContainerRef.current.clientWidth, height: chartContainerRef.current.clientHeight });
            }
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            chart.remove();
        };
    }, []);

    // 4. Update Data & Markers
    useEffect(() => {
        if (seriesRef.current && displayedBars.length > 0) {
            seriesRef.current.setData(displayedBars);

            // Markers
            if (trade) {
                const markers = [];
                const lastBar = displayedBars[displayedBars.length - 1];
                const lastTime = lastBar.time;

                const entryTime = new Date(trade.entry_time).getTime() / 1000;
                const exitTime = new Date(trade.exit_time).getTime() / 1000;

                // Show entry if passed
                if (lastTime >= entryTime) {
                    markers.push({
                        time: entryTime,
                        position: trade.side === 'BUY' ? 'belowBar' : 'aboveBar',
                        color: '#38bdf8',
                        shape: trade.side === 'BUY' ? 'arrowUp' : 'arrowDown',
                        text: `ENTRY ${trade.side} @ ${trade.entry_price}`
                    });
                }

                // Show exit if passed
                if (lastTime >= exitTime) {
                    markers.push({
                        time: exitTime,
                        position: trade.side === 'BUY' ? 'aboveBar' : 'belowBar',
                        color: '#fbbf24',
                        shape: trade.side === 'BUY' ? 'arrowDown' : 'arrowUp', // Exit BUY is Sell
                        text: `EXIT (${trade.pnl_net.toFixed(2)})`
                    });
                }
                seriesRef.current.setMarkers(markers);
            }

            // Auto-scroll to latest bar if playing
            if (isPlaying) {
                chartRef.current?.timeScale().scrollToPosition(0, false); // 0 is rightmost? No, offset. 
                // Actually fitContent or scrollToRealTime?
                // scrollToPosition(0) keeps right edge at latest.
            }
        }
    }, [displayedBars, trade, isPlaying]);

    // 5. Timer Loop
    useEffect(() => {
        if (isPlaying) {
            timerRef.current = setInterval(() => {
                setCurrentIndex(prev => {
                    const next = prev + 1;
                    if (next >= allBars.length) {
                        setIsPlaying(false);
                        return prev;
                    }
                    return next;
                });
            }, 1000 / (speed * 2)); // Base speed adjustment
        } else {
            clearInterval(timerRef.current);
        }
        return () => clearInterval(timerRef.current);
    }, [isPlaying, speed, allBars.length]);

    // 6. Sync Display
    useEffect(() => {
        if (allBars.length > 0) {
            setDisplayedBars(allBars.slice(0, currentIndex + 1));
        }
    }, [currentIndex, allBars]);

    // Helpers
    const handleProgressChange = (e) => {
        const val = parseInt(e.target.value);
        setCurrentIndex(val);
    };

    if (!tradeId) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm" style={{ position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.85)', zIndex: 1000, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-[90vw] h-[85vh] flex flex-col overflow-hidden" style={{ background: '#0f172a', border: '1px solid #334155', borderRadius: '12px', width: '90vw', height: '85vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>

                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-slate-700" style={{ padding: '1rem', borderBottom: '1px solid #334155', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <div>
                        <h2 className="text-xl font-bold text-slate-100" style={{ margin: 0, color: '#f1f5f9', fontSize: '1.25rem' }}>Trade Replay</h2>
                        <div className="text-sm text-slate-400" style={{ color: '#94a3b8', fontSize: '0.875rem' }}>
                            {trade ? `${trade.symbol} • ${trade.side} • ${new Date(trade.entry_time).toLocaleString()}` : "Loading..."}
                        </div>
                    </div>
                    <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                        <select
                            value={timeframe}
                            onChange={(e) => setTimeframe(e.target.value)}
                            style={{ background: '#1e293b', color: '#fff', border: '1px solid #334155', padding: '0.25rem 0.5rem', borderRadius: '4px' }}
                        >
                            <option value="1m">1m</option>
                            <option value="5m">5m</option>
                            <option value="15m">15m</option>
                            <option value="1h">1h</option>
                        </select>
                        <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-full transition-colors" style={{ background: 'transparent', border: 'none', color: '#94a3b8', cursor: 'pointer' }}>
                            <X size={24} />
                        </button>
                    </div>
                </div>

                {/* Chart Area */}
                <div className="flex-1 relative" style={{ flex: 1, position: 'relative' }}>
                    {loading && <div style={{ position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#94a3b8' }}>Loading candles...</div>}
                    {!loading && allBars.length === 0 && (
                        <div style={{ position: 'absolute', inset: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: '#f87171' }}>
                            <p>No bars found for timeframe <strong>{timeframe}</strong></p>
                            <p style={{ fontSize: '0.8rem', color: '#94a3b8' }}>Try switching timeframe or checking if market data exists.</p>
                        </div>
                    )}
                    <div ref={chartContainerRef} style={{ width: '100%', height: '100%' }} />
                </div>

                {/* Controls */}
                <div className="p-4 border-t border-slate-700 bg-slate-800/50" style={{ padding: '1rem', borderTop: '1px solid #334155', background: '#1e293b' }}>
                    <div className="flex items-center gap-4" style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                        <button
                            onClick={() => setIsPlaying(!isPlaying)}
                            className="p-3 bg-blue-600 hover:bg-blue-500 rounded-full text-white shadow-lg transition-all"
                            style={{ background: isPlaying ? '#ef4444' : '#3b82f6', border: 'none', borderRadius: '50%', width: '48px', height: '48px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', color: '#fff' }}
                        >
                            {isPlaying ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" ml="2px" />}
                        </button>

                        <div className="flex items-center gap-2 bg-slate-800 rounded-lg p-1 border border-slate-700" style={{ display: 'flex', gap: '0.5rem', background: '#0f172a', padding: '0.25rem', borderRadius: '8px', border: '1px solid #334155' }}>
                            {[1, 5, 10, 20].map(s => (
                                <button
                                    key={s}
                                    onClick={() => setSpeed(s)}
                                    className={`px-3 py-1 rounded text-sm font-medium transition-colors ${speed === s ? 'bg-slate-700 text-blue-400' : 'text-slate-400 hover:text-slate-200'}`}
                                    style={{
                                        background: speed === s ? '#334155' : 'transparent',
                                        color: speed === s ? '#60a5fa' : '#94a3b8',
                                        border: 'none',
                                        borderRadius: '4px',
                                        padding: '0.25rem 0.75rem',
                                        cursor: 'pointer'
                                    }}
                                >
                                    {s}x
                                </button>
                            ))}
                        </div>

                        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                            <input
                                type="range"
                                min="0"
                                max={allBars.length > 0 ? allBars.length - 1 : 0}
                                value={currentIndex}
                                onChange={handleProgressChange}
                                style={{ width: '100%', accentColor: '#3b82f6' }}
                            />
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.75rem', color: '#64748b' }}>
                                <span>{displayedBars.length > 0 ? new Date(displayedBars[displayedBars.length - 1].time * 1000).toLocaleString() : '--:--'}</span>
                                <span>{allBars.length > 0 ? Math.round((currentIndex / allBars.length) * 100) : 0}%</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
