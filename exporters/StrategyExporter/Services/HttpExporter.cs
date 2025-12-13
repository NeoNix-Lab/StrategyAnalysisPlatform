#nullable enable
using System;
using System.Collections.Generic;
using System.Net.Http;
using System.Net.Http.Json;
using System.Text.Json;
using System.Threading.Tasks;
using StrategyExporter.DTOs;

namespace StrategyExporter.Services
{
    public class HttpExporter : IExporter
    {
        private readonly HttpClient _client;
        private readonly string _baseUrl;

        // Caches to avoid resending static data if needed, though interfaces are stateless-ish
        private string? _activeStrategyId;
        private string? _activeRunId;

        public HttpExporter(string baseUrl = "http://localhost:8000")
        {
            _baseUrl = baseUrl.TrimEnd('/');
            _client = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(5) // Fast fail for trading systems
            };
        }



        public async Task<string> StartRunAsync(RunRegistrationDto runInfo)
        {
            this._activeStrategyId = runInfo.StrategyId;

            var response = await _client.PostAsJsonAsync($"{_baseUrl}/api/runs/start", runInfo);
            response.EnsureSuccessStatusCode();

            var result = await response.Content.ReadFromJsonAsync<RunResponseDto>();
            if (result == null || string.IsNullOrEmpty(result.RunId))
                throw new Exception("Backend returned invalid RunId");

            _activeRunId = result.RunId;
            return _activeRunId;
        }

        public async Task ExportBarsAsync(IEnumerable<BarDto> bars)
        {
            using var response = await _client.PostAsJsonAsync($"{_baseUrl}/api/ingest/stream", new { bars = bars });
            // We might want to just log errors instead of throwing to avoid crashing strategy logic?
            // For now, let the caller (Buffer) handle exceptions.
            response.EnsureSuccessStatusCode();
        }

        public async Task ExportOrdersAsync(IEnumerable<OrderDto> orders)
        {
            foreach (var order in orders)
            {
                OverrideRunId(order);
            }
            using var response = await _client.PostAsJsonAsync($"{_baseUrl}/api/ingest/stream", new { orders = orders });
            response.EnsureSuccessStatusCode();
        }

        public async Task ExportTradesAsync(IEnumerable<TradeDto> trades)
        {
            foreach (var trade in trades)
            {
                OverrideRunId(trade);
            }
            using var response = await _client.PostAsJsonAsync($"{_baseUrl}/api/ingest/stream", new { trades = trades });
            response.EnsureSuccessStatusCode();
        }

        public async Task StopRunAsync(string runId)
        {
            // Optional: notify backend of run completion
            using var response = await _client.PostAsync($"{_baseUrl}/api/runs/{runId}/stop", null);
        }

        public void Dispose()
        {
            _client?.Dispose();
        }

        private void OverrideRunId(OrderDto obj)
        {
            // Do NOT change OrderId. Backend handles idempotency.
            obj.RunId = _activeRunId;
            obj.StrategyId = _activeStrategyId;
        }
        private void OverrideRunId(TradeDto obj)
        {
            // Do NOT change TradeId.
            obj.RunId = _activeRunId;
            obj.StrategyId = _activeStrategyId;
        }
    }
}
