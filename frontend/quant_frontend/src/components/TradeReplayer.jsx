import React, { useEffect, useRef, useState } from 'react';
import { createChart, ColorType } from 'lightweight-charts';
import { Play, Pause, FastForward, SkipBack, X, Gauge, AlertCircle, Clock } from 'lucide-react';

export const TradeReplayer = ({ tradeId, onClose }) => {
    const [trade, setTrade] = useState(null);
    const [allBars, setAllBars] = useState([]);
    const [displayedBars, setDisplayedBars] = useState([]);

    // Playback State
    const [isPlaying, setIsPlaying] = useState(false);
    const [speed, setSpeed] = useState(1);
    const [currentIndex, setCurrentIndex] = useState(0);

    // Config State
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [timeframe, setTimeframe] = useState(null);
    const [availableTimeframes, setAvailableTimeframes] = useState([]);

    const chartContainerRef = useRef();
    const chartRef = useRef();
    const seriesRef = useRef();
    const timerRef = useRef();

    // 1. Fetch Trade Details & Available Series
    useEffect(() => {
        const fetchTradeAndMetadata = async () => {
            try {
                // A. Fetch Trade
                const resTrade = await fetch(`/api/trades/${tradeId}`);
                if (!resTrade.ok) throw new Error('Failed to fetch trade details');
                const tradeData = await resTrade.json();
                setTrade(tradeData);

                // B. Fetch Available Series for this Run
                const resSeries = await fetch(`/api/runs/${tradeData.run_id}/series`);

                let validTimeframes = ['1m', '5m', '15m', '1h']; // Default Fallback

                if (resSeries.ok) {
                    const seriesList = await resSeries.json();
                    if (Array.isArray(seriesList) && seriesList.length > 0) {
                        // Extract unique timeframes
                        validTimeframes = [...new Set(seriesList.map(s => s.timeframe))];
                        // Sort logic can be complex (1m, 5m etc), simple alpha sort for now
                        validTimeframes.sort();
                    }
                }

                setAvailableTimeframes(validTimeframes);

                // C. Determine Initial Timeframe
                // Priority: 1. Trade's explicit timeframe -> 2. First available -> 3. '1m'
                if (tradeData.timeframe && validTimeframes.includes(tradeData.timeframe)) {
                    setTimeframe(tradeData.timeframe);
                } else if (validTimeframes.length > 0) {
                    setTimeframe(validTimeframes[0]);
                } else {
                    setTimeframe('1m');
                }

            } catch (err) {
                console.error(err);
                setError("Impossibile caricare i dettagli del trade.");
            }
        };
        if (tradeId) fetchTradeAndMetadata();
    }, [tradeId]);

    // 2. Fetch Bars
    useEffect(() => {
        if (!trade || !timeframe) return;

        const fetchBars = async () => {
            setLoading(true);
            setError(null);
            try {
                // Buffer: 2 hours before, 2 hours after
                const entryTime = new Date(trade.entry_time);
                const exitTime = new Date(trade.exit_time);

                if (isNaN(entryTime.getTime()) || isNaN(exitTime.getTime())) {
                    throw new Error("Date del trade non valide");
                }

                const start = new Date(entryTime.getTime() - 2 * 60 * 60 * 1000).toISOString();
                const end = new Date(exitTime.getTime() + 2 * 60 * 60 * 1000).toISOString();

                const url = `/api/bars/?run_id=${trade.run_id}&symbol=${trade.symbol}&timeframe=${timeframe}&start_utc=${start}&end_utc=${end}`;
                const res = await fetch(url);

                if (!res.ok) {
                    const errData = await res.json().catch(() => ({}));
                    throw new Error(errData.detail || "Errore nel caricamento dei dati di mercato");
                }

                const data = await res.json();

                if (!Array.isArray(data) || data.length === 0) {
                    setAllBars([]);
                    setDisplayedBars([]);
                    // Do not stop loading if we are just switching timeframe, 
                    // BUT here we assume no data = empty chart.
                    setLoading(false);
                    return;
                }

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

                // Initial Position: 30 bars before entry
                const entryTs = entryTime.getTime() / 1000;
                const entryIndex = formatted.findIndex(b => b.time >= entryTs);
                const startIndex = Math.max(0, entryIndex - 30);

                setCurrentIndex(startIndex);
                setDisplayedBars(formatted.slice(0, startIndex + 1));
                setLoading(false);

            } catch (err) {
                console.error(err);
                setError(err.message || "Errore sconosciuto");
                setLoading(false);
            }
        };

        fetchBars();
    }, [trade, timeframe]);

    // 3. Initialize Chart
    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: '#0f172a' }, // Slate-900
                textColor: '#94a3b8',
                fontFamily: "'JetBrains Mono', monospace",
            },
            grid: {
                vertLines: { color: '#1e293b' }, // Slate-800
                horzLines: { color: '#1e293b' }
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderColor: '#334155'
            },
            rightPriceScale: {
                borderColor: '#334155'
            },
            crosshair: {
                vertLine: { labelBackgroundColor: '#334155' },
                horzLine: { labelBackgroundColor: '#334155' },
            },
        });

        const series = chart.addCandlestickSeries({
            upColor: '#10b981', // Emerald-500
            downColor: '#ef4444', // Red-500
            borderVisible: false,
            wickUpColor: '#10b981',
            wickDownColor: '#ef4444'
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
                        color: '#38bdf8', // Sky-400
                        shape: trade.side === 'BUY' ? 'arrowUp' : 'arrowDown',
                        text: `ENTRY ${trade.side} @ ${trade.entry_price}`
                    });
                }

                // Show exit if passed
                if (lastTime >= exitTime) {
                    markers.push({
                        time: exitTime,
                        position: trade.side === 'BUY' ? 'aboveBar' : 'belowBar',
                        color: '#fbbf24', // Amber-400
                        shape: trade.side === 'BUY' ? 'arrowDown' : 'arrowUp', // Exit BUY is Sell
                        text: `EXIT (${trade.pnl_net.toFixed(2)})`
                    });
                }
                seriesRef.current.setMarkers(markers);
            }

            // Auto-scroll to latest bar if playing
            if (isPlaying) {
                chartRef.current?.timeScale().scrollToPosition(0, false);
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
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-md animate-in fade-in duration-200">
            <div className="bg-slate-900 border border-slate-700 rounded-xl shadow-2xl w-[95vw] h-[90vh] flex flex-col overflow-hidden animate-in zoom-in-95 duration-200 relative">

                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/50">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-blue-500/10 rounded-lg border border-blue-500/20 text-blue-400">
                            <Clock size={20} />
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-slate-100 leading-tight">Trade Replay</h2>
                            <div className="flex items-center gap-2 text-xs text-slate-400">
                                {trade ? (
                                    <>
                                        <span className={`px-1.5 py-0.5 rounded font-bold ${trade.side === 'BUY' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                                            {trade.side}
                                        </span>
                                        <span className="font-mono text-slate-300">{trade.symbol}</span>
                                        <span className="text-slate-600">•</span>
                                        <span>{new Date(trade.entry_time).toLocaleString()}</span>
                                    </>
                                ) : "Caricamento dettagli..."}
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center bg-slate-800/80 rounded-lg p-1 border border-slate-700">
                            {availableTimeframes.map(tf => (
                                <button
                                    key={tf}
                                    onClick={() => setTimeframe(tf)}
                                    className={`px-3 py-1 text-xs font-medium rounded-md transition-all ${timeframe === tf ? 'bg-slate-600 text-white shadow-sm' : 'text-slate-400 hover:text-slate-200 hover:bg-slate-700/50'}`}
                                >
                                    {tf}
                                </button>
                            ))}
                        </div>
                        <button
                            onClick={onClose}
                            className="p-2 text-slate-400 hover:text-white hover:bg-slate-800/50 rounded-full transition-colors"
                        >
                            <X size={24} />
                        </button>
                    </div>
                </div>

                {/* Chart Area */}
                <div className="flex-1 relative bg-slate-950">
                    {loading && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 gap-3 z-10 bg-slate-900/50 backdrop-blur-sm">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-accent"></div>
                            <span className="text-sm font-medium">Caricamento storico candele...</span>
                        </div>
                    )}

                    {error && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center p-6 z-10 bg-slate-900/80 backdrop-blur-sm">
                            <div className="max-w-md w-full bg-slate-900 border border-red-500/20 rounded-xl p-6 text-center shadow-2xl">
                                <div className="mx-auto w-12 h-12 bg-red-500/10 rounded-full flex items-center justify-center text-red-400 mb-4">
                                    <AlertCircle size={24} />
                                </div>
                                <h3 className="text-lg font-bold text-white mb-2">Errore Caricamento</h3>
                                <p className="text-sm text-slate-400 mb-4">{error}</p>
                                <div className="flex justify-center gap-3">
                                    <button
                                        onClick={onClose}
                                        className="px-4 py-2 rounded-lg bg-slate-800 text-slate-300 hover:bg-slate-700 text-sm font-medium transition-colors"
                                    >
                                        Chiudi
                                    </button>
                                </div>
                            </div>
                        </div>
                    )}

                    {!loading && !error && allBars.length === 0 && (
                        <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 gap-2 z-10">
                            <AlertCircle size={32} className="text-slate-600" />
                            <p>Nessuna candela trovata per il timeframe <strong>{timeframe}</strong></p>
                            <p className="text-xs text-slate-500">Prova a cambiare timeframe o verifica se i dati di mercato sono disponibili.</p>
                            <div className="mt-2 text-[10px] text-slate-600 font-mono">
                                RunID: {trade?.run_id?.substring(0, 8)}...
                            </div>
                        </div>
                    )}

                    <div ref={chartContainerRef} className="w-full h-full" />
                </div>

                {/* Player Controls */}
                <div className="p-4 border-t border-slate-800 bg-slate-900/90 backdrop-blur">
                    <div className="flex items-center gap-6">
                        {/* Play/Pause */}
                        <button
                            onClick={() => setIsPlaying(!isPlaying)}
                            disabled={allBars.length === 0}
                            className={`
                                w-12 h-12 rounded-full flex items-center justify-center shadow-lg transition-transform active:scale-95
                                ${isPlaying
                                    ? 'bg-red-500 hover:bg-red-600 text-white shadow-red-500/20'
                                    : 'bg-accent hover:bg-blue-600 text-white shadow-blue-500/20'
                                }
                                disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none
                            `}
                        >
                            {isPlaying ? <Pause size={20} fill="currentColor" /> : <Play size={20} fill="currentColor" className="ml-0.5" />}
                        </button>

                        {/* Speed Control */}
                        <div className="flex items-center gap-2 bg-slate-950 rounded-lg p-1 border border-slate-800">
                            <div className="px-2 text-xs font-bold text-slate-500 uppercase tracking-wider flex items-center gap-1">
                                <Gauge size={12} /> Speed
                            </div>
                            {[1, 5, 10, 20].map(s => (
                                <button
                                    key={s}
                                    onClick={() => setSpeed(s)}
                                    className={`
                                        w-8 h-7 text-xs font-bold rounded flex items-center justify-center transition-colors
                                        ${speed === s ? 'bg-slate-800 text-accent shadow-sm' : 'text-slate-500 hover:text-slate-300 hover:bg-slate-800/50'}
                                    `}
                                >
                                    {s}x
                                </button>
                            ))}
                        </div>

                        {/* Timeline Scrubber */}
                        <div className="flex-1 flex flex-col gap-1.5">
                            <input
                                type="range"
                                min="0"
                                max={allBars.length > 0 ? allBars.length - 1 : 0}
                                value={currentIndex}
                                onChange={handleProgressChange}
                                disabled={allBars.length === 0}
                                className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-accent hover:accent-accent/80 transition-all"
                            />
                            <div className="flex justify-between items-center text-[10px] uppercase font-bold tracking-wider text-slate-500">
                                <span>
                                    {displayedBars.length > 0
                                        ? new Date(displayedBars[displayedBars.length - 1].time * 1000).toLocaleString()
                                        : '--:--'
                                    }
                                </span>
                                <span>
                                    {allBars.length > 0
                                        ? `${Math.round((currentIndex / allBars.length) * 100)}%`
                                        : '0%'
                                    }
                                </span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};
