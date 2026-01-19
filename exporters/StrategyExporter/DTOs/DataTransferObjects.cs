#nullable enable
using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace StrategyExporter.DTOs
{
    public class ConnectionCreateDto
    {
        [JsonPropertyName("connection_id")]
        public string? ConnectionId { get; set; }

        [JsonPropertyName("user_id")]
        public string? UserId { get; set; }

        [JsonPropertyName("name")]
        public string? Name { get; set; }

        [JsonPropertyName("platform")]
        public string Platform { get; set; } = string.Empty;

        [JsonPropertyName("mode")]
        public string Mode { get; set; } = "LIVE";

        [JsonPropertyName("status")]
        public string Status { get; set; } = "PENDING";

        [JsonPropertyName("account_id")]
        public string? AccountId { get; set; }

        [JsonPropertyName("capabilities_json")]
        public Dictionary<string, object>? CapabilitiesJson { get; set; }

        [JsonPropertyName("config_json")]
        public Dictionary<string, object>? ConfigJson { get; set; }

        [JsonPropertyName("secrets_json")]
        public Dictionary<string, object>? SecretsJson { get; set; }

        [JsonPropertyName("meta_json")]
        public Dictionary<string, object>? MetaJson { get; set; }
    }

    public class ConnectionHeartbeatDto
    {
        [JsonPropertyName("heartbeat_utc")]
        public DateTime? HeartbeatUtc { get; set; }

        [JsonPropertyName("status")]
        public string? Status { get; set; }

        [JsonPropertyName("latency_ms")]
        public double? LatencyMs { get; set; }
    }
}
