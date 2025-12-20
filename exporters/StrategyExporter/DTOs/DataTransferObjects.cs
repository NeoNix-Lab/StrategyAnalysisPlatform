#nullable enable
using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace StrategyExporter.DTOs
{
    public class StrategyRegistrationDto
    {
        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;

        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        [JsonPropertyName("default_parameters")]
        public Dictionary<string, object> Parameters { get; set; } = new();

        // Explicitly set strategy_id if we want to force/claim a specific ID from client side
        [JsonPropertyName("strategy_id")]
        public string? StrategyId { get; set; }
    }

    public class StrategyResponseDto
    {
        [JsonPropertyName("strategy_id")]
        public string StrategyId { get; set; } = string.Empty;

        [JsonPropertyName("name")]
        public string Name { get; set; } = string.Empty;
    }

    public class RunRegistrationDto
    {
        [JsonPropertyName("strategy_id")]
        public string StrategyId { get; set; } = string.Empty;

        [JsonPropertyName("parameters")]
        public Dictionary<string, object> Parameters { get; set; } = new();

        [JsonPropertyName("start_time")]
        public DateTime StartTime { get; set; } = DateTime.UtcNow;

        [JsonPropertyName("status")]
        public string Status { get; set; } = "RUNNING";
    }

    public class RunResponseDto
    {
        [JsonPropertyName("run_id")]
        public string RunId { get; set; } = string.Empty;

        [JsonPropertyName("status")]
        public string Status { get; set; } = string.Empty;
    }

    public class BarDto
    {
        [JsonPropertyName("run_id")]
        public string RunId { get; set; } = string.Empty; // Not strictly in BarBase schemas but useful for context if needed, though usually implicit in ingestion endpoint

        [JsonPropertyName("symbol")]
        public string Symbol { get; set; } = string.Empty;

        [JsonPropertyName("timeframe")]
        public string Timeframe { get; set; } = "1m";

        [JsonPropertyName("timestamp")]
        public DateTime Timestamp { get; set; }

        [JsonPropertyName("end_time")]
        public DateTime? EndTime { get; set; }

        [JsonPropertyName("open")]
        public double Open { get; set; }

        [JsonPropertyName("high")]
        public double High { get; set; }

        [JsonPropertyName("low")]
        public double Low { get; set; }

        [JsonPropertyName("close")]
        public double Close { get; set; }

        [JsonPropertyName("volume")]
        public double Volume { get; set; }

        [JsonPropertyName("open_interest")]
        public double? OpenInterest { get; set; }
    }

    public class OrderDto
    {
        [JsonPropertyName("order_id")]
        public string OrderId { get; set; } = string.Empty;

        [JsonPropertyName("run_id")]
        public string RunId { get; set; } = string.Empty;

        [JsonPropertyName("strategy_id")]
        public string StrategyId { get; set; } = string.Empty;

        [JsonPropertyName("account_id")]
        public string AccountId { get; set; } = string.Empty;

        [JsonPropertyName("symbol")]
        public string Symbol { get; set; } = string.Empty;

        [JsonPropertyName("side")]
        public string Side { get; set; } = string.Empty; // BUY, SELL

        [JsonPropertyName("order_type")]
        public string OrderType { get; set; } = "MARKET"; // MARKET, LIMIT, STOP...

        [JsonPropertyName("quantity")]
        public double Quantity { get; set; }

        [JsonPropertyName("price")]
        public double? Price { get; set; }

        [JsonPropertyName("stop_price")]
        public double? StopPrice { get; set; }

        [JsonPropertyName("status")]
        public string Status { get; set; } = "NEW";

        [JsonPropertyName("submit_time")]
        public DateTime SubmitTime { get; set; } = DateTime.UtcNow;

        [JsonPropertyName("time_in_force")]
        public string? TimeInForce { get; set; } = "GTC";
    }

    public class ExecutionDto
    {
        [JsonPropertyName("run_id")]
        public string RunId { get; set; } = string.Empty;

        [JsonPropertyName("execution_id")]
        public string ExecutionId { get; set; } = string.Empty;

        [JsonPropertyName("order_id")]
        public string OrderId { get; set; } = string.Empty;

        [JsonPropertyName("exec_utc")]
        public DateTime ExecUtc { get; set; }

        [JsonPropertyName("price")]
        public double Price { get; set; }

        [JsonPropertyName("quantity")]
        public double Quantity { get; set; }

        [JsonPropertyName("fee")]
        public double? Fee { get; set; }

        [JsonPropertyName("fee_currency")]
        public string? FeeCurrency { get; set; }

        [JsonPropertyName("liquidity")]
        public string? Liquidity { get; set; }

        [JsonPropertyName("position_impact")]
        public string? PositionImpact { get; set; } = "UNKNOWN";

        [JsonPropertyName("extra_json")]
        public Dictionary<string, object>? ExtraJson { get; set; }
    }
}
