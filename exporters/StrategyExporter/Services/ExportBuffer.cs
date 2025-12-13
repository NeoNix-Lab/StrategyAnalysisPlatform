#nullable enable
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using StrategyExporter.DTOs;

namespace StrategyExporter.Services
{
    /// <summary>
    /// Thread-safe buffer that accumulates data and flushes it to the exporter in batches.
    /// Remove SQLite dependency, purely focuses on IExporter (HTTP).
    /// </summary>
    public sealed class ExportBuffer : IDisposable
    {
        private readonly IExporter _exporter;
        private readonly int _batchSize;

        // Locks
        private readonly object _barsLock = new();
        private readonly object _ordersLock = new();
        private readonly object _tradesLock = new();

        // Buffers
        private List<BarDto> _bars = new();
        private List<OrderDto> _orders = new();
        private List<TradeDto> _trades = new();

        // Async coordination
        private readonly SemaphoreSlim _writeLock = new(1, 1);
        private readonly List<Task> _pendingExports = new();
        private readonly object _pendingLock = new();
        private bool _disposed;

        public ExportBuffer(IExporter exporter, int batchSize = 100)
        {
            _exporter = exporter ?? throw new ArgumentNullException(nameof(exporter));
            _batchSize = Math.Max(1, batchSize);
        }

        // --- Add Methods ---

        public void AddBar(BarDto bar)
        {
            if (bar == null) return;
            List<BarDto>? toExport = null;
            lock (_barsLock)
            {
                _bars.Add(bar);
                if (_bars.Count >= _batchSize)
                {
                    toExport = _bars;
                    _bars = new List<BarDto>();
                }
            }
            if (toExport != null) EnqueueExport(async () => await _exporter.ExportBarsAsync(toExport));
        }

        public void AddOrder(OrderDto order)
        {
            if (order == null) return;
            List<OrderDto>? toExport = null;
            lock (_ordersLock)
            {
                _orders.Add(order);
                if (_orders.Count >= _batchSize)
                {
                    toExport = _orders;
                    _orders = new List<OrderDto>();
                }
            }
            if (toExport != null) EnqueueExport(async () => await _exporter.ExportOrdersAsync(toExport));
        }

        public void AddTrade(TradeDto trade)
        {
            if (trade == null) return;
            List<TradeDto>? toExport = null;
            lock (_tradesLock)
            {
                _trades.Add(trade);
                if (_trades.Count >= _batchSize)
                {
                    toExport = _trades;
                    _trades = new List<TradeDto>();
                }
            }
            if (toExport != null) EnqueueExport(async () => await _exporter.ExportTradesAsync(toExport));
        }

        // --- Export Orchestration ---

        private void EnqueueExport(Func<Task> exportAction)
        {
            if (_disposed) return;

            Task task = Task.Run(async () =>
            {
                // Serialize access to the underlying exporter if needed
                await _writeLock.WaitAsync();
                try
                {
                    await exportAction().ConfigureAwait(false);
                }
                catch (Exception)
                {
                    // Log error? For now we swallow to prevent crashing
                }
                finally
                {
                    _writeLock.Release();
                }
            });

            lock (_pendingLock)
            {
                _pendingExports.Add(task);
                // cleanup finished tasks
                _pendingExports.RemoveAll(t => t.IsCompleted);
            }
        }

        public async Task FlushAsync()
        {
            if (_disposed) return;

            // 1. Snapshot remaining buffers
            List<BarDto>? barsSnap;
            List<OrderDto>? ordersSnap;
            List<TradeDto>? tradesSnap;

            lock (_barsLock) { barsSnap = _bars.Count > 0 ? _bars : null; _bars = new List<BarDto>(); }
            lock (_ordersLock) { ordersSnap = _orders.Count > 0 ? _orders : null; _orders = new List<OrderDto>(); }
            lock (_tradesLock) { tradesSnap = _trades.Count > 0 ? _trades : null; _trades = new List<TradeDto>(); }

            // 2. Wait for current running uploads
            Task[] pending;
            lock (_pendingLock) { pending = _pendingExports.ToArray(); }
            if (pending.Length > 0)
            {
                try { await Task.WhenAll(pending); } catch { }
            }

            // 3. Upload snapshots
            await _writeLock.WaitAsync();
            try
            {
                if (barsSnap != null) await _exporter.ExportBarsAsync(barsSnap);
                if (ordersSnap != null) await _exporter.ExportOrdersAsync(ordersSnap);
                if (tradesSnap != null) await _exporter.ExportTradesAsync(tradesSnap);
            }
            catch { }
            finally
            {
                _writeLock.Release();
            }
        }

        public void Dispose()
        {
            if (_disposed) return;
            _disposed = true;

            try
            {
                // Synchronously flush best effort
                FlushAsync().GetAwaiter().GetResult();
            }
            catch { }

            _writeLock.Dispose();
            // Exporter is not disposed here because we received it via DI/Constructor
            // We do not own it strictly speaking, but for this strategy cleanup it's safer to not dispose shared
            // However, HttpExporter is created per strategy run, so we might want to dispose it if we owned it.
            // For now, let's explicitely NOT dispose the injected dependency to follow DI pattern 
            // unless we change design. But HttpExporter is Disposable...
            // Let's assume the caller manages the exporter's lifecycle or we will changing it.
            // Actually, in the strategy we create it and pass it. So strategy should dispose it.
        }
    }
}
