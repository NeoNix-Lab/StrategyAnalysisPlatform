using System;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using System.Threading.Tasks;
using TradingPlatform.BusinessLayer;

namespace StrategyExporterTemplate.Services
{
    public class HttpExporter : IDisposable
    {
        private readonly HttpClient _client;
        private readonly string _baseUrl;

        public HttpExporter(string baseUrl)
        {
            _baseUrl = baseUrl.TrimEnd('/');
            _client = new HttpClient();
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

        public void Dispose()
        {
            _client?.Dispose();
        }
    }
}
