#nullable enable
using System;
using System.Net.Http;
using System.Net.Http.Json;
using System.Threading.Tasks;
using StrategyExporter.DTOs;

namespace StrategyExporter.Services
{
    public sealed class ConnectionAdapter : IDisposable
    {
        private readonly HttpClient _client;
        private readonly string _baseUrl;

        public ConnectionAdapter(string baseUrl = "http://localhost:8000", string? apiKey = null)
        {
            _baseUrl = baseUrl.TrimEnd('/');
            _client = new HttpClient
            {
                Timeout = TimeSpan.FromSeconds(5)
            };

            if (!string.IsNullOrWhiteSpace(apiKey))
            {
                _client.DefaultRequestHeaders.Add("X-API-Key", apiKey);
            }
        }

        public void SetApiKey(string apiKey)
        {
            _client.DefaultRequestHeaders.Remove("X-API-Key");
            if (!string.IsNullOrWhiteSpace(apiKey))
            {
                _client.DefaultRequestHeaders.Add("X-API-Key", apiKey);
            }
        }

        public async Task RegisterAsync(ConnectionCreateDto connection)
        {
            if (connection == null) throw new ArgumentNullException(nameof(connection));
            var response = await _client.PostAsJsonAsync($"{_baseUrl}/api/connections", connection);
            response.EnsureSuccessStatusCode();
        }

        public async Task HeartbeatAsync(string connectionId, ConnectionHeartbeatDto heartbeat)
        {
            if (string.IsNullOrWhiteSpace(connectionId)) throw new ArgumentNullException(nameof(connectionId));
            heartbeat ??= new ConnectionHeartbeatDto();
            var response = await _client.PostAsJsonAsync($"{_baseUrl}/api/connections/{connectionId}/heartbeat", heartbeat);
            response.EnsureSuccessStatusCode();
        }

        public void Dispose()
        {
            _client?.Dispose();
        }
    }
}
