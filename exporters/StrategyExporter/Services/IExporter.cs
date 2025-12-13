using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using StrategyExporter.DTOs;

namespace StrategyExporter.Services
{
    public interface IExporter : IDisposable
    {
        // Handshake: Start Run (Strategy auto-registered if needed)
        Task<string> StartRunAsync(RunRegistrationDto runInfo);

        // Data Streaming
        Task ExportBarsAsync(IEnumerable<BarDto> bars);
        Task ExportOrdersAsync(IEnumerable<OrderDto> orders);
        Task ExportTradesAsync(IEnumerable<TradeDto> trades);

        // Lifecycle
        Task StopRunAsync(string runId);
    }
}
