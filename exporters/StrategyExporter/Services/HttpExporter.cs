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



        public async Task SendAsync<T>(string uri, T payload)
        {
            var response = await _client.PostAsJsonAsync($"{_baseUrl}/{uri}", payload);
            response.EnsureSuccessStatusCode();
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
            using var response = await _client.PostAsJsonAsync($"{_baseUrl}/api/ingest/batch/bars", bars);
            response.EnsureSuccessStatusCode();
        }

        public async Task ExportOrdersAsync(IEnumerable<OrderDto> orders)
        {
            foreach (var order in orders)
            {
                OverrideRunId(order);
            }
            using var response = await _client.PostAsJsonAsync($"{_baseUrl}/api/ingest/batch/orders", orders);
            response.EnsureSuccessStatusCode();
        }

        public async Task ExportTradesAsync(IEnumerable<ExecutionDto> trades)
        {
            foreach (var trade in trades)
            {
                OverrideRunId(trade);
            }
            using var response = await _client.PostAsJsonAsync($"{_baseUrl}/api/ingest/batch/executions", trades);
            response.EnsureSuccessStatusCode();
        }

        public async Task StopRunAsync(string runId)
        {
            // Call finalize endpoint
            using var response = await _client.PostAsync($"{_baseUrl}/api/runs/{runId}/stop", null);
            response.EnsureSuccessStatusCode();
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
        private void OverrideRunId(ExecutionDto obj)
        {
            // Do NOT change TradeId.
            obj.RunId = _activeRunId;
            // StrategyId might not be in ExecutionDto if we removed it? Let's check DTO.
            // DTO has no StrategyId anymore.
        }
    }
}
