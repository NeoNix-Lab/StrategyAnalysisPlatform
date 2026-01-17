# Socket Message Examples

This file contains practical examples of socket messages for the Strategy Analysis Platform.

## 1. Ingest Event Messages

### Order Event
```json
{
  "msg_id": "550e8400-e29b-41d4-a716-446655440000",
  "msg_type": "ingest_event",
  "timestamp": "2026-01-03T12:41:00.000Z",
  "source": "quantower-connector",
  "target": "api-gateway",
  "payload": {
    "run_id": "run-123",
    "event_type": "order",
    "event_utc": "2026-01-03T12:41:00.000Z",
    "payload_json": {
      "order_id": "ord-456",
      "symbol": "BTCUSDT",
      "side": "BUY",
      "order_type": "LIMIT",
      "quantity": 0.1,
      "price": 45000.0
    },
    "received_utc": "2026-01-03T12:41:00.100Z"
  }
}
```

### Execution Event
```json
{
  "msg_id": "550e8400-e29b-41d4-a716-446655440001",
  "msg_type": "ingest_event",
  "timestamp": "2026-01-03T12:41:05.000Z",
  "source": "quantower-connector",
  "target": "api-gateway",
  "payload": {
    "run_id": "run-123",
    "event_type": "execution",
    "event_utc": "2026-01-03T12:41:05.000Z",
    "payload_json": {
      "execution_id": "exec-789",
      "order_id": "ord-456",
      "symbol": "BTCUSDT",
      "side": "BUY",
      "quantity": 0.1,
      "price": 45000.0,
      "commission": 0.045
    },
    "received_utc": "2026-01-03T12:41:05.100Z"
  }
}
```

### Market Data Event
```json
{
  "msg_id": "550e8400-e29b-41d4-a716-446655440002",
  "msg_type": "ingest_event",
  "timestamp": "2026-01-03T12:41:10.000Z",
  "source": "market-data-feed",
  "target": null,
  "payload": {
    "run_id": "run-123",
    "event_type": "market_data",
    "event_utc": "2026-01-03T12:41:10.000Z",
    "payload_json": {
      "series_id": "series-btc-1m",
      "symbol": "BTCUSDT",
      "timeframe": "1m",
      "bar": {
        "ts_utc": "2026-01-03T12:41:00.000Z",
        "open": 45000.0,
        "high": 45050.0,
        "low": 44980.0,
        "close": 45020.0,
        "volume": 1.23
      }
    },
    "received_utc": "2026-01-03T12:41:10.100Z"
  }
}
```

## 2. Logging Messages

### Info Log
```json
{
  "msg_id": "550e8400-e29b-41d4-a716-446655440003",
  "msg_type": "log_record",
  "timestamp": "2026-01-03T12:41:15.000Z",
  "source": "trade-service",
  "target": "log-aggregator",
  "payload": {
    "timestamp": "2026-01-03T12:41:15.000Z",
    "level": "INFO",
    "name": "trade_service",
    "message": "Trade reconstructed successfully",
    "meta": {
      "trade_id": "trade-101",
      "run_id": "run-123",
      "pnl": 12.5,
      "duration_ms": 45000
    }
  }
}
```

### Error Log
```json
{
  "msg_id": "550e8400-e29b-41d4-a716-446655440004",
  "msg_type": "log_record",
  "timestamp": "2026-01-03T12:41:20.000Z",
  "source": "api-gateway",
  "target": "log-aggregator",
  "payload": {
    "timestamp": "2026-01-03T12:41:20.000Z",
    "level": "ERROR",
    "name": "order_handler",
    "message": "Failed to process order: Invalid quantity",
    "meta": {
      "order_id": "ord-457",
      "error_code": "INVALID_QUANTITY",
      "client_ip": "192.168.1.100"
    }
  }
}
```

## 3. System Messages

### Heartbeat
```json
{
  "msg_id": "550e8400-e29b-41d4-a716-446655440005",
  "msg_type": "heartbeat",
  "timestamp": "2026-01-03T12:41:25.000Z",
  "source": "quantower-connector",
  "target": "health-monitor",
  "payload": {
    "status": "alive",
    "timestamp": "2026-01-03T12:41:25.000Z"
  }
}
```

### Error Message
```json
{
  "msg_id": "550e8400-e29b-41d4-a716-446655440006",
  "msg_type": "error",
  "timestamp": "2026-01-03T12:41:30.000Z",
  "source": "market-data-feed",
  "target": "api-gateway",
  "payload": {
    "code": "CONNECTION_LOST",
    "message": "Lost connection to exchange API",
    "details": {
      "exchange": "binance",
      "last_successful_ping": "2026-01-03T12:40:00.000Z",
      "retry_count": 3
    }
  }
}
```

### Acknowledgment
```json
{
  "msg_id": "550e8400-e29b-41d4-a716-446655440007",
  "msg_type": "ack",
  "timestamp": "2026-01-03T12:41:35.000Z",
  "source": "api-gateway",
  "target": "quantower-connector",
  "payload": {
    "acknowledged_msg_id": "550e8400-e29b-41d4-a716-446655440000",
    "timestamp": "2026-01-03T12:41:35.000Z"
  }
}
```

## 4. Domain Entity Messages

### Strategy Instance Update
```json
{
  "msg_id": "550e8400-e29b-41d4-a716-446655440008",
  "msg_type": "ingest_event",
  "timestamp": "2026-01-03T12:41:40.000Z",
  "source": "strategy-manager",
  "target": "api-gateway",
  "payload": {
    "run_id": "run-123",
    "event_type": "strategy_event",
    "event_utc": "2026-01-03T12:41:40.000Z",
    "payload_json": {
      "event": "instance_updated",
      "instance": {
        "instance_id": "inst-789",
        "strategy_id": "str-123",
        "instance_name": "BTC Trend Following",
        "parameters_json": {
          "fast_period": 12,
          "slow_period": 26,
          "signal_period": 9
        },
        "symbols_json": ["BTCUSDT", "ETHUSDT"],
        "timeframe": "1h",
        "venue": "binance",
        "created_utc": "2026-01-03T10:00:00.000Z"
      }
    },
    "received_utc": "2026-01-03T12:41:40.100Z"
  }
}
```

### OCO Group Creation
```json
{
  "msg_id": "550e8400-e29b-41d4-a716-446655440009",
  "msg_type": "ingest_event",
  "timestamp": "2026-01-03T12:41:45.000Z",
  "source": "order-manager",
  "target": "api-gateway",
  "payload": {
    "run_id": "run-123",
    "event_type": "order",
    "event_utc": "2026-01-03T12:41:45.000Z",
    "payload_json": {
      "event": "oco_group_created",
      "oco_group": {
        "oco_group_id": "oco-111",
        "run_id": "run-123",
        "created_utc": "2026-01-03T12:41:45.000Z",
        "label": "BTC Entry with SL/TP",
        "order_ids": ["ord-456", "ord-457", "ord-458"],
        "extra_json": {
          "entry_order": "ord-456",
          "stop_loss": "ord-457",
          "take_profit": "ord-458"
        }
      }
    },
    "received_utc": "2026-01-03T12:41:45.100Z"
  }
}
```

## 5. Batch Processing

### Multiple Ingest Events
```json
{
  "msg_id": "550e8400-e29b-41d4-a716-446655440010",
  "msg_type": "ingest_event",
  "timestamp": "2026-01-03T12:42:00.000Z",
  "source": "batch-processor",
  "target": "api-gateway",
  "payload": {
    "run_id": "run-123",
    "event_type": "system_event",
    "event_utc": "2026-01-03T12:42:00.000Z",
    "payload_json": {
      "event": "batch_ingest",
      "events": [
        {
          "event_type": "order",
          "order_id": "ord-500",
          "symbol": "ETHUSDT",
          "side": "SELL",
          "quantity": 1.0
        },
        {
          "event_type": "execution",
          "execution_id": "exec-501",
          "order_id": "ord-500",
          "quantity": 1.0,
          "price": 2800.0
        }
      ]
    },
    "received_utc": "2026-01-03T12:42:00.100Z"
  }
}
```
