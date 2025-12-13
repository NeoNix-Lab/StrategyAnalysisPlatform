// Copyright QUANTOWER LLC. © 2017-2023. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.Metrics;
using System.Linq;
using System.Threading.Tasks;
using TradingPlatform.BusinessLayer;
using StrategyExporterTemplate.DTOs;
using StrategyExporterTemplate.Services;

namespace StrategyExporterTemplate
{
    /// An example of blank strategy. Add your code, compile it and run via Strategy Runner panel in the assigned trading terminal.
    /// Information about API you can find here: http://api.quantower.com
    /// Code samples: https://github.com/Quantower/Examples 
    /// </summary>
    public class StrategyExporterTemplate : Strategy
    {
        #region //--- ATTRIBUTES ---
        [InputParameter("Symbol", 0)]
        public Symbol InputSymbol;

        [InputParameter("Account", 1)]
        public Account InputAccount;

        [InputParameter("Trade quantity", 2, 0.0, double.MaxValue, 0.01, 2)]
        public double TradeQuantity = 1.0;

        [InputParameter("Load Data From", 200)]
        private DateTime loadDataFrom;

        [InputParameter("Aggregation period", 7)]
        public Period AggregationPeriod = Period.MIN1;

        [InputParameter("Enable HTTP Export", 12)]
        public bool EnableHttpExport = true;

        [InputParameter("HTTP Export Endpoint", 13)]
        public string HttpExportEndpoint = "http://localhost:8000";
        #endregion //--- ATTRIBUTES ---

        #region //--- FIELDS ---
        private HistoricalData historicalData;

        // Export
        private HttpExporter _exporter;
        private string _runId = string.Empty;
        private string _instanceId = string.Empty;
        private string _strategyId = string.Empty;
        private volatile bool _isExporting = false;
        // Removed TCS, we will block OnRun instead

        #endregion

        public StrategyExporterTemplate()
            : base()
        {
            this.Name = "StrategyExporterTemplate";
            this.Description = "My strategy's annotation";
        }

        protected override void OnCreated()
        {
        }

        protected override void OnRun()
        {
            Core.Instance.Loggers.Log($"{this.Name}: OnRun Triggered", LoggingLevel.System);

            // 1. Synchronous Blocking Initialization
            if (this.EnableHttpExport)
            {
                Core.Instance.Loggers.Log($"{this.Name}: Starting Exporter Init (Blocking)...", LoggingLevel.System);
                // This will block until the Run is successfully created on the backend
                InitializeExporterSync();
                this._isExporting = true;
            }

            this.historicalData = this.InputSymbol.GetHistory(this.AggregationPeriod, this.loadDataFrom);
            this.historicalData.NewHistoryItem += this.HistoricalData_NewHistoryItem;

            Core.Instance.TradeAdded += this.Instance_TradeAdded;
            Core.Instance.OrderAdded += this.Instance_OrderAdded;
        }

        private void Instance_OrderAdded(Order ord)
        {
            // Log everything first
            Core.Instance.Loggers.Log($"[Pre-Check] OrderAdded: {ord.Id} Sym:{ord.Symbol.Name} State:{ord.State} Exporting:{_isExporting}", LoggingLevel.System);

            if (this._isExporting)
            {
                // Check Symbol Name instead of object reference
                // Relaxed check for debugging:
                if (ord.Symbol.Name == this.InputSymbol.Name)
                {
                    Core.Instance.Loggers.Log($"[DBG] Exporting Order: {ord.Id}", LoggingLevel.System);
                    ExportOrder(ord);
                }
                else
                {
                    Core.Instance.Loggers.Log($"[DBG] Skipped Order: {ord.Id} ({ord.Symbol.Name} vs {this.InputSymbol.Name})", LoggingLevel.System);
                }
            }
        }

        private void Instance_TradeAdded(Trade obj)
        {
            if (this._isExporting)
            {
                Core.Instance.Loggers.Log($"[DBG] TradeAdded: {obj.Id} Sym:{obj.Symbol.Name} State:{obj.State}", LoggingLevel.System);

                if (obj.Symbol.Name == this.InputSymbol.Name) // && obj.State != BusinessObjectState.Fake)
                {
                    Core.Instance.Loggers.Log($"[DBG] Exporting Execution: {obj.Id}", LoggingLevel.System);
                    ExportExecution(obj);
                }
            }
        }

        private void HistoricalData_NewHistoryItem(object sender, HistoryEventArgs e)
        {
            // Example Logic
            if (this._isExporting)
            {
                ExportBar((HistoryItem)e.HistoryItem);
            }

            // Simple trading logic for demo
            var positions = Core.Instance.Positions.Where(p => p.Symbol == this.InputSymbol).ToArray();
            if (positions.Length == 0)
            {
                if (this.historicalData[1][PriceType.Open] < this.historicalData[1][PriceType.Close])
                    this.PlaceOrder(Side.Buy);
            }
        }

        protected override void OnStop()
        {
            if (_exporter != null)
            {
                _exporter.Dispose();
            }

            this.historicalData.NewHistoryItem -= this.HistoricalData_NewHistoryItem;
            this.historicalData.Dispose();

            Core.Instance.TradeAdded -= this.Instance_TradeAdded;
            Core.Instance.OrderAdded -= this.Instance_OrderAdded;
        }

        protected override void OnRemove()
        {
        }

        private void InitializeExporterSync()
        {
            this._exporter = new HttpExporter(this.HttpExportEndpoint);

            try
            {
                // 1. IDs
                this._strategyId = this.Name;

                // Deterministic Instance ID based on Parameters
                string paramsString = $"{this.Name}_{InputAccount.Name}_{InputSymbol.Name}_{AggregationPeriod}";
                this._instanceId = CreateMD5(paramsString);

                this._runId = Guid.NewGuid().ToString();

                // 2. Strategy - Blocking Calls
                _exporter.SendAsync("api/ingest/event/strategy_create", new StrategyCreateDto
                {
                    StrategyId = _strategyId,
                    Name = this.Name,
                    Notes = this.Description
                }).GetAwaiter().GetResult();

                // 3. Instance
                _exporter.SendAsync("api/ingest/event/instance_create", new StrategyInstanceCreateDto
                {
                    InstanceId = _instanceId,
                    StrategyId = _strategyId,
                    InstanceName = $"{this.Name}_{InputAccount.Name}",
                    Parameters = new Dictionary<string, object> {
                            { "Symbol", InputSymbol.Name },
                            { "Timeframe", AggregationPeriod.ToString() }
                        },
                    Symbol = InputSymbol.Name,
                    Timeframe = AggregationPeriod.ToString(),
                    AccountId = InputAccount.Name,
                    Venue = InputAccount.Name
                }).GetAwaiter().GetResult();

                // 4. Run
                _exporter.SendAsync("api/ingest/event/run_start", new StrategyRunCreateDto
                {
                    RunId = _runId,
                    InstanceId = _instanceId,
                    RunType = "LIVE", // Default
                    StartUtc = DateTime.UtcNow,
                    Status = "RUNNING",
                    EngineVersion = "0.1.0",
                    InitialBalance = InputAccount.Balance,
                    BaseCurrency = InputAccount.AccountCurrency.Id,
                }).GetAwaiter().GetResult();

                Core.Instance.Loggers.Log($"{this.Name} Export initialized. RunID: {_runId}", LoggingLevel.System);
            }
            catch (Exception ex)
            {
                Core.Instance.Loggers.Log($"{this.Name} Failed to initialize exporter: {ex.Message}", LoggingLevel.Error);
                // If init fails, we probably shouldn't set _isExporting to true in OnRun, 
                // but currently OnRun just proceeds. 
                throw; // Throwing here might stop the strategy, which is good if export is mandatory.
            }
        }

        // --- Export Methods ---

        private void ExportOrder(Order order)
        {
            // Fire and forget, no need to wait for TCS, init is already done.
            Task.Run(async () =>
            {
                var dto = new OrderDto
                {
                    RunId = _runId,
                    StrategyId = _strategyId,
                    OrderId = order.Id,
                    ParentOrderId = null, // TODO: Extract from order if possible
                    Symbol = order.Symbol?.Name ?? "Unknown",
                    AccountId = order.Account?.Name ?? "Unknown",
                    Side = order.Side.ToString().ToUpperInvariant(),
                    OrderType = MapOrderType(order.OrderTypeId), // Need mapping logic
                    TimeInForce = order.TimeInForce.ToString(),
                    Quantity = order.TotalQuantity,
                    Price = double.IsNaN(order.Price) ? null : order.Price,
                    StopPrice = (order.StopLoss?.Price).HasValue && !double.IsNaN(order.StopLoss.Price) ? order.StopLoss.Price : null,
                    Status = MapOrderStatus(order.Status),
                    SubmitUtc = order.LastUpdateTime == default ? DateTime.UtcNow : order.LastUpdateTime,
                    PositionImpact = "UNKNOWN"
                };
                await _exporter.SendAsync("api/ingest/event/order", dto);
            });
        }

        private void ExportExecution(Trade trade)
        {
            Task.Run(async () =>
            {
                // No need to wait anymore
                var dto = new ExecutionDto
                {
                    RunId = _runId,
                    ExecutionId = trade.Id,
                    OrderId = trade.OrderId,
                    ExecUtc = trade.DateTime,
                    Price = trade.Price,
                    Quantity = trade.Quantity,
                    Fee = trade.Fee?.Value,
                    FeeCurrency = trade.Fee?.Asset.UniqueId ?? "UNKNOWN",
                    Liquidity = "UNKNOWN"
                };
                await _exporter.SendAsync("api/ingest/event/execution", dto);
            });
        }

        private void ExportBar(HistoryItem bar)
        {
            Task.Run(async () =>
            {
                var dto = new BarDto
                {
                    RunId = _runId,
                    Symbol = this.InputSymbol.Name,
                    Timeframe = this.AggregationPeriod.ToString(),
                    Venue = this.InputAccount.Name, // Account Name usually serves as Venue in Quantower for some connections, or use Connection info
                    Provider = "Quantower",
                    TsUtc = bar.TimeLeft,
                    Open = bar[PriceType.Open],
                    High = bar[PriceType.High],
                    Low = bar[PriceType.Low],
                    Close = bar[PriceType.Close],
                    Volume = bar[PriceType.Volume], // or bar[PriceType.Volume]? check SDK
                    // Volumetric:
                    // Volumetric = new Dictionary<string, object> { ... }
                };
                await _exporter.SendAsync("api/ingest/event/bar", dto);
            });
        }

        // --- Helpers ---

        private void PlaceOrder(Side side)
        {
            var result = Core.Instance.PlaceOrder(new PlaceOrderRequestParameters
            {
                Account = this.InputAccount,
                Symbol = this.InputSymbol,
                Side = side,
                Quantity = this.TradeQuantity,
                OrderTypeId = OrderType.Market,
                TimeInForce = TimeInForce.GTC,
                StopLoss = SlTpHolder.CreateSL(100, PriceMeasurement.Offset, isTrailing: true),
                TakeProfit = SlTpHolder.CreateTP(100, PriceMeasurement.Offset)
            });
        }

        private string MapOrderStatus(OrderStatus status)
        {
            // Quantower OrderStatus: Opened, Filled, Cancelled, Refused...
            switch (status)
            {
                case OrderStatus.Opened: return "NEW";
                case OrderStatus.Filled: return "FILLED";
                case OrderStatus.Cancelled: return "CANCELED";
                case OrderStatus.Refused: return "REJECTED";
                default: return "UNKNOWN";
            }
        }

        private string MapOrderType(string typeId)
        {
            // Generic mapping
            if (typeId == OrderType.Market) return "MARKET";
            if (typeId == OrderType.Limit) return "LIMIT";
            if (typeId == OrderType.Stop) return "STOP";
            return "MARKET"; // default
        }

        public static string CreateMD5(string input)
        {
            // Use .NET MD5 to create a consistent hash
            using (System.Security.Cryptography.MD5 md5 = System.Security.Cryptography.MD5.Create())
            {
                byte[] inputBytes = System.Text.Encoding.ASCII.GetBytes(input);
                byte[] hashBytes = md5.ComputeHash(inputBytes);

                // Convert the byte array to hexadecimal string
                System.Text.StringBuilder sb = new System.Text.StringBuilder();
                for (int i = 0; i < hashBytes.Length; i++)
                {
                    sb.Append(hashBytes[i].ToString("X2"));
                }
                return sb.ToString();
            }
        }

        protected override void OnInitializeMetrics(Meter meter)
        {
            meter.CreateObservableGauge("Balance", () =>
            {
                return this.InputAccount != null ? this.InputAccount.Balance : 0.0;
            });
        }
    }
}