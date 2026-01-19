using System;
using System.Net.Http;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using TradingPlatform.BusinessLayer;
using StrategyExporterTemplate.DTOs;

namespace StrategyExporterTemplate.Services
{
    public class HttpExporter : IDisposable
    {
        private readonly HttpClient _client;
        private readonly string _baseUrl;

        public HttpExporter(string baseUrl, string apiKey = null)
        {
            _baseUrl = baseUrl.TrimEnd('/');
            _client = new HttpClient();
            if (!string.IsNullOrWhiteSpace(apiKey))
            {
                _client.DefaultRequestHeaders.Add("X-API-Key", apiKey);
            }
        }

        public async Task SendAsync<T>(string endpoint, T data)
        {
            // Simply fire and forget with logging, or await if needed
            try
            {
                var json = JsonSerializer.Serialize(data);
                var content = new StringContent(json, Encoding.UTF8, "application/json");

                // Using PostAsync in a way that doesn't block the UI/Strategy thread too much?
                // Actually if we await here, we rely on the caller to await or Task.Run
                var response = await _client.PostAsync($"{_baseUrl}/{endpoint}", content);

                if (!response.IsSuccessStatusCode)
                {
                    var msg = await response.Content.ReadAsStringAsync();
                    Core.Instance.Loggers.Log($"Exporter Error [{endpoint}]: {response.StatusCode} {msg}", LoggingLevel.Error);
                }
            }
            catch (Exception ex)
            {
                Core.Instance.Loggers.Log($"Exporter Exception [{endpoint}]: {ex.Message}", LoggingLevel.Error);
            }
        }

        public async Task<IngestRunStartResponseDto> StartRunAsync(IngestRunStartRequestDto data)
        {
            var response = await SendForResponseAsync<IngestRunStartRequestDto, IngestRunStartResponseDto>(
                "api/ingest/run/start",
                data
            );
            if (response == null)
            {
                throw new InvalidOperationException("Run start response was empty.");
            }
            return response;
        }

        public async Task ExportBarsAsync(IEnumerable<BarDto> bars)
        {
            await SendAsync("api/ingest/batch/bars", bars);
        }

        public async Task ExportOrdersAsync(IEnumerable<OrderDto> orders)
        {
            await SendAsync("api/ingest/batch/orders", orders);
        }

        public async Task ExportExecutionsAsync(IEnumerable<ExecutionDto> executions)
        {
            await SendAsync("api/ingest/batch/executions", executions);
        }

        public async Task StopRunAsync(string runId)
        {
            try
            {
                var response = await _client.PostAsync($"{_baseUrl}/api/runs/{runId}/stop", null);
                if (!response.IsSuccessStatusCode)
                {
                    var msg = await response.Content.ReadAsStringAsync();
                    Core.Instance.Loggers.Log($"Exporter Error [StopRun]: {response.StatusCode} {msg}", LoggingLevel.Error);
                }
            }
            catch (Exception ex)
            {
                Core.Instance.Loggers.Log($"Exporter Exception [StopRun]: {ex.Message}", LoggingLevel.Error);
            }
        }

        public void Dispose()
        {
            _client?.Dispose();
        }

        private async Task<TResponse> SendForResponseAsync<TRequest, TResponse>(string endpoint, TRequest data)
        {
            var json = JsonSerializer.Serialize(data);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var response = await _client.PostAsync($"{_baseUrl}/{endpoint}", content);
            var body = await response.Content.ReadAsStringAsync();
            if (!response.IsSuccessStatusCode)
            {
                Core.Instance.Loggers.Log($"Exporter Error [{endpoint}]: {response.StatusCode} {body}", LoggingLevel.Error);
                throw new InvalidOperationException($"Exporter request failed: {response.StatusCode}");
            }

            if (string.IsNullOrWhiteSpace(body))
            {
                return default;
            }

            return JsonSerializer.Deserialize<TResponse>(body, new JsonSerializerOptions
            {
                PropertyNameCaseInsensitive = true
            });
        }
    }
}
