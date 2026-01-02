from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum
import uuid

# ============================================================================
# Common Types (Socket-optimized)
# ============================================================================

class SocketMessageType(str, Enum):
    """Message types for socket communication"""
    INGEST_EVENT = "ingest_event"
    LOG_RECORD = "log_record"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    ACK = "ack"

class SocketMessage(BaseModel):
    """Base socket message wrapper"""
    msg_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    msg_type: SocketMessageType
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    source: str = Field(..., description="Source service/client identifier")
    target: Optional[str] = Field(None, description="Target service/client (None=broadcast)")
    payload: Dict[str, Any] = Field(..., description="Message payload")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ============================================================================
# Ingest Event Models (Socket-optimized)
# ============================================================================

class IngestEventType(str, Enum):
    """Types of ingest events"""
    ORDER = "order"
    EXECUTION = "execution"
    ACCOUNT_UPDATE = "account_update"
    POSITION_UPDATE = "position_update"
    MARKET_DATA = "market_data"
    STRATEGY_EVENT = "strategy_event"
    SYSTEM_EVENT = "system_event"

class IngestEvent(BaseModel):
    """Socket-optimized ingest event"""
    run_id: str = Field(..., description="Strategy run ID")
    event_type: IngestEventType
    event_utc: datetime
    payload_json: Dict[str, Any] = Field(..., description="Raw event data")
    received_utc: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ============================================================================
# Logging Models (Socket-optimized)
# ============================================================================

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class LogRecord(BaseModel):
    """Socket-optimized log record"""
    timestamp: datetime
    level: LogLevel
    name: str = Field(..., description="Logger name (service/module)")
    message: str
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ============================================================================
# Domain Models (Socket-optimized versions of core entities)
# ============================================================================

class StrategyInstance(BaseModel):
    """Socket-optimized strategy instance"""
    instance_id: str
    strategy_id: str
    instance_name: Optional[str] = None
    parameters_json: Dict[str, Any]
    symbols_json: List[str]  # Required array of symbols
    timeframe: Optional[str] = None
    account_id: Optional[str] = None
    venue: Optional[str] = None
    created_utc: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class StrategyRun(BaseModel):
    """Socket-optimized strategy run"""
    run_id: str
    instance_id: str
    run_type: str  # BACKTEST, LIVE, PAPER, REPLAY
    start_utc: datetime
    end_utc: Optional[datetime] = None
    status: str  # RUNNING, COMPLETED, FAILED, CANCELLED
    engine_version: Optional[str] = None
    data_source: Optional[str] = None
    initial_balance: Optional[float] = None
    base_currency: Optional[str] = None
    metrics_json: Optional[Dict[str, Any]] = None
    created_utc: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Order(BaseModel):
    """Socket-optimized order"""
    order_id: str
    run_id: str
    symbol: str
    side: str  # BUY, SELL
    order_type: str  # MARKET, LIMIT, STOP, STOP_LIMIT
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: Optional[str] = None
    status: str  # PENDING, FILLED, CANCELLED, REJECTED
    created_utc: datetime
    updated_utc: Optional[datetime] = None
    filled_quantity: float = 0.0
    average_price: Optional[float] = None
    commission: float = 0.0
    external_id: Optional[str] = None
    meta_json: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Execution(BaseModel):
    """Socket-optimized execution"""
    execution_id: str
    run_id: str
    order_id: str
    symbol: str
    side: str  # BUY, SELL
    quantity: float
    price: float
    commission: float = 0.0
    executed_utc: datetime
    external_id: Optional[str] = None
    meta_json: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class OrderOcoGroup(BaseModel):
    """Socket-optimized OCO group"""
    oco_group_id: str
    run_id: str
    created_utc: datetime
    label: Optional[str] = None
    order_ids: List[str]  # Array of order IDs
    extra_json: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RunSeries(BaseModel):
    """Socket-optimized run series"""
    series_id: str
    symbol: str
    timeframe: str
    venue: Optional[str] = None
    provider: Optional[str] = None
    run_ids: List[str]  # Array of run IDs (for API compatibility)
    created_utc: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class RunSeriesBar(BaseModel):
    """Socket-optimized run series bar"""
    series_id: str
    ts_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float = 0.0
    volumetric_json: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class Trade(BaseModel):
    """Socket-optimized trade"""
    trade_id: str
    run_id: str
    symbol: str
    side: str  # LONG, SHORT
    entry_time: datetime
    exit_time: datetime
    entry_price: float
    exit_price: float
    quantity: float
    pnl_net: float
    pnl_gross: Optional[float] = None
    commission: float = 0.0
    mae: Optional[float] = None  # Maximum Adverse Excursion
    mfe: Optional[float] = None  # Maximum Favorable Excursion
    duration_seconds: Optional[float] = None
    regime_trend: Optional[str] = None
    regime_volatility: Optional[str] = None
    extra_json: Optional[Dict[str, Any]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

# ============================================================================
# Socket Message Factory Functions
# ============================================================================

def create_ingest_message(source: str, run_id: str, event_type: IngestEventType, payload: Dict[str, Any], target: Optional[str] = None) -> SocketMessage:
    """Create an ingest event socket message"""
    event = IngestEvent(
        run_id=run_id,
        event_type=event_type,
        event_utc=payload.get("event_utc", datetime.utcnow()),
        payload_json=payload
    )
    
    return SocketMessage(
        msg_type=SocketMessageType.INGEST_EVENT,
        source=source,
        target=target,
        payload=event.dict()
    )

def create_log_message(source: str, level: LogLevel, logger_name: str, message: str, meta: Optional[Dict[str, Any]] = None, target: Optional[str] = None) -> SocketMessage:
    """Create a log record socket message"""
    log_record = LogRecord(
        timestamp=datetime.utcnow(),
        level=level,
        name=logger_name,
        message=message,
        meta=meta or {}
    )
    
    return SocketMessage(
        msg_type=SocketMessageType.LOG_RECORD,
        source=source,
        target=target,
        payload=log_record.dict()
    )

def create_heartbeat(source: str, target: Optional[str] = None) -> SocketMessage:
    """Create a heartbeat message"""
    return SocketMessage(
        msg_type=SocketMessageType.HEARTBEAT,
        source=source,
        target=target,
        payload={"status": "alive", "timestamp": datetime.utcnow().isoformat()}
    )

def create_error_message(source: str, error_code: str, error_message: str, details: Optional[Dict[str, Any]] = None, target: Optional[str] = None) -> SocketMessage:
    """Create an error message"""
    return SocketMessage(
        msg_type=SocketMessageType.ERROR,
        source=source,
        target=target,
        payload={
            "code": error_code,
            "message": error_message,
            "details": details or {}
        }
    )

def create_ack_message(source: str, original_msg_id: str, target: Optional[str] = None) -> SocketMessage:
    """Create an acknowledgment message"""
    return SocketMessage(
        msg_type=SocketMessageType.ACK,
        source=source,
        target=target,
        payload={
            "acknowledged_msg_id": original_msg_id,
            "timestamp": datetime.utcnow().isoformat()
        }
    )
