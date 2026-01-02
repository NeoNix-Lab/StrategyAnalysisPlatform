# Socket Contracts for Strategy Analysis Platform

This directory contains Pydantic models optimized for real-time socket communication between services.

## Files

- **socket_models.py**: Complete set of socket-optimized models for:
  - Ingest events (orders, executions, market data, strategy events)
  - Logging records (structured logging)
  - Domain entities (StrategyInstance, StrategyRun, Order, Execution, Trade, etc.)
  - Socket message envelope and factory functions

## Key Features

### Socket-Optimized Design
- All models use Pydantic for validation and serialization
- ISO format timestamps for JSON compatibility
- Enum types for type safety
- Optional fields marked explicitly
- Factory functions for common message types

### Message Types
- **INGEST_EVENT**: Real-time trading events
- **LOG_RECORD**: Structured logging
- **HEARTBEAT**: Connection health checks
- **ERROR**: Error propagation
- **ACK**: Message acknowledgments

### Domain Models
All core entities from the updated SQLAlchemy models are included:
- StrategyInstance (with symbols_json array)
- StrategyRun
- Order, Execution, Trade
- OrderOcoGroup (with order_ids array)
- RunSeries, RunSeriesBar (shared series design)

## Usage Examples

```python
from socket_models import (
    create_ingest_message, 
    create_log_message,
    IngestEventType,
    LogLevel,
    SocketMessage
)

# Send ingest event
msg = create_ingest_message(
    source="quantower-connector",
    run_id="run-123",
    event_type=IngestEventType.ORDER,
    payload={"symbol": "BTCUSDT", "side": "BUY", "quantity": 0.1}
)

# Send log record
log_msg = create_log_message(
    source="api-gateway",
    level=LogLevel.INFO,
    logger_name="trade_service",
    message="Trade reconstructed successfully",
    meta={"trade_id": "trade-456", "run_id": "run-123"}
)
```

## Integration

These models are designed to work with:
- WebSocket connections
- Message queues (Redis, RabbitMQ)
- Event streaming platforms
- Real-time notifications

All models are compatible with the updated SQLAlchemy models and JSON contracts in this package.
