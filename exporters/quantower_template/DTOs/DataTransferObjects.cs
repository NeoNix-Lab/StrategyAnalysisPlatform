using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace StrategyExporterTemplate.DTOs
{
    public class StrategyCreateDto
    {
        [JsonPropertyName("strategy_id")] public string StrategyId { get; set; }
        [JsonPropertyName("name")] public string Name { get; set; }
        [JsonPropertyName("version")] public string Version { get; set; }
        [JsonPropertyName("vendor")] public string Vendor { get; set; }
        [JsonPropertyName("source_ref")] public string SourceRef { get; set; }
        [JsonPropertyName("notes")] public string Notes { get; set; }
    }

    public class StrategyInstanceCreateDto
    {
        [JsonPropertyName("instance_id")] public string InstanceId { get; set; }
        [JsonPropertyName("strategy_id")] public string StrategyId { get; set; }
        [JsonPropertyName("instance_name")] public string InstanceName { get; set; }
        [JsonPropertyName("parameters_json")] public Dictionary<string, object> Parameters { get; set; }
        [JsonPropertyName("symbol")] public string Symbol { get; set; }
        [JsonPropertyName("symbols_json")] public List<string> Symbols { get; set; }
        [JsonPropertyName("timeframe")] public string Timeframe { get; set; }
        [JsonPropertyName("account_id")] public string AccountId { get; set; }
        [JsonPropertyName("venue")] public string Venue { get; set; }
    }

    public class StrategyRunCreateDto
    {
        [JsonPropertyName("run_id")] public string RunId { get; set; }
        [JsonPropertyName("instance_id")] public string InstanceId { get; set; }
        [JsonPropertyName("run_type")] public string RunType { get; set; }
        [JsonPropertyName("start_utc")] public DateTime StartUtc { get; set; }
        [JsonPropertyName("status")] public string Status { get; set; }
        [JsonPropertyName("engine_version")] public string EngineVersion { get; set; }
        [JsonPropertyName("data_source")] public string DataSource { get; set; }
        [JsonPropertyName("initial_balance")] public double? InitialBalance { get; set; }
        [JsonPropertyName("base_currency")] public string BaseCurrency { get; set; }
        [JsonPropertyName("metrics_json")] public Dictionary<string, object> Metrics { get; set; }
    }

    public class OrderDto
    {
        [JsonPropertyName("run_id")] public string RunId { get; set; }
        [JsonPropertyName("order_id")] public string OrderId { get; set; }
        [JsonPropertyName("strategy_id")] public string StrategyId { get; set; }
        [JsonPropertyName("parent_order_id")] public string ParentOrderId { get; set; }
        [JsonPropertyName("symbol")] public string Symbol { get; set; }
        [JsonPropertyName("account_id")] public string AccountId { get; set; }
        [JsonPropertyName("side")] public string Side { get; set; }
        [JsonPropertyName("order_type")] public string OrderType { get; set; }
        [JsonPropertyName("time_in_force")] public string TimeInForce { get; set; }
        [JsonPropertyName("quantity")] public double Quantity { get; set; }
        [JsonPropertyName("price")] public double? Price { get; set; }
        [JsonPropertyName("stop_price")] public double? StopPrice { get; set; }
        [JsonPropertyName("status")] public string Status { get; set; }
        [JsonPropertyName("submit_utc")] public DateTime SubmitUtc { get; set; }
        [JsonPropertyName("client_tag")] public string ClientTag { get; set; }
        [JsonPropertyName("position_impact")] public string PositionImpact { get; set; }
        [JsonPropertyName("extra_json")] public Dictionary<string, object> Extra { get; set; }
    }

    public class ExecutionDto
    {
        [JsonPropertyName("run_id")] public string RunId { get; set; }
        [JsonPropertyName("execution_id")] public string ExecutionId { get; set; }
        [JsonPropertyName("order_id")] public string OrderId { get; set; }
        [JsonPropertyName("exec_utc")] public DateTime ExecUtc { get; set; }
        [JsonPropertyName("price")] public double Price { get; set; }
        [JsonPropertyName("quantity")] public double Quantity { get; set; }
        [JsonPropertyName("fee")] public double? Fee { get; set; }
        [JsonPropertyName("fee_currency")] public string FeeCurrency { get; set; }
        [JsonPropertyName("liquidity")] public string Liquidity { get; set; }
        [JsonPropertyName("position_impact")] public string PositionImpact { get; set; }
        [JsonPropertyName("extra_json")] public Dictionary<string, object> Extra { get; set; }
    }

    public class BarDto
    {
        [JsonPropertyName("run_id")] public string RunId { get; set; }
        [JsonPropertyName("symbol")] public string Symbol { get; set; }
        [JsonPropertyName("timeframe")] public string Timeframe { get; set; }
        [JsonPropertyName("venue")] public string Venue { get; set; }
        [JsonPropertyName("provider")] public string Provider { get; set; }
        [JsonPropertyName("ts_utc")] public DateTime TsUtc { get; set; }
        [JsonPropertyName("open")] public double Open { get; set; }
        [JsonPropertyName("high")] public double High { get; set; }
        [JsonPropertyName("low")] public double Low { get; set; }
        [JsonPropertyName("close")] public double Close { get; set; }
        [JsonPropertyName("volume")] public double Volume { get; set; }
        [JsonPropertyName("volumetric_json")] public Dictionary<string, object> Volumetric { get; set; }
    }
}
