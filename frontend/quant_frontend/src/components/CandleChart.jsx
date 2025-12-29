import { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

export const CandleChart = ({ data, trade, width = 600, height = 400 }) => {
    const chartContainerRef = useRef();

    useEffect(() => {
        if (!chartContainerRef.current) return;

        const chart = createChart(chartContainerRef.current, {
            width: width,
            height: height,
            layout: {
                background: { type: ColorType.Solid, color: '#1e293b' },
                textColor: '#94a3b8',
            },
            grid: {
                vertLines: { color: '#334155' },
                horzLines: { color: '#334155' },
            },
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
            },
        });

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#4ade80',
            downColor: '#f87171',
            borderVisible: false,
            wickUpColor: '#4ade80',
            wickDownColor: '#f87171',
        });

        // Format data for lightweight-charts
        // Expects: { time: '2018-12-22', open: 75.16, high: 82.84, low: 36.16, close: 45.72 }
        // API returns ISO timestamps, lightweight-charts handles unix timestamp best for intraday
        const formattedData = data.map(d => ({
            time: new Date(d.timestamp).getTime() / 1000,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
        }));

        candlestickSeries.setData(formattedData);

        // Add markers for Entry and Exit if trade provided
        if (trade) {
            const markers = [];

            // Entry Marker
            markers.push({
                time: new Date(trade.entry_time).getTime() / 1000,
                position: trade.side === 'BUY' ? 'belowBar' : 'aboveBar',
                color: '#38bdf8',
                shape: trade.side === 'BUY' ? 'arrowUp' : 'arrowDown',
                text: `ENTRY ${trade.side}`,
            });

            // Exit Marker
            markers.push({
                time: new Date(trade.exit_time).getTime() / 1000,
                position: trade.side === 'BUY' ? 'aboveBar' : 'belowBar', // Exit is opposite
                color: '#fbbf24',
                shape: trade.side === 'BUY' ? 'arrowDown' : 'arrowUp', // Exit BUY means Sell
                text: `EXIT (${trade.pnl_net.toFixed(1)}€)`,
            });

            candlestickSeries.setMarkers(markers);
        }

        chart.timeScale().fitContent();

        return () => {
            chart.remove();
        };
    }, [data, trade, width, height]);

    return <div ref={chartContainerRef} />;
};
