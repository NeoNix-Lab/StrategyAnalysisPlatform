from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

# --- Enums ---

class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    MIT = "MIT"

class OrderStatus(str, Enum):
    NEW = "NEW"
    WORKING = "WORKING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"

class PositionImpactType(str, Enum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    REDUCE = "REDUCE"
    REVERSE = "REVERSE"
    UNKNOWN = "UNKNOWN"

class ConnectionStatus(str, Enum):
    PENDING = "PENDING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    ERROR = "ERROR"
    DISABLED = "DISABLED"

class ConnectionMode(str, Enum):
    LIVE = "LIVE"
    PAPER = "PAPER"

# --- Input Schemas (Create/Ingest) ---

class StrategyParameter(BaseModel):
    name: str
    label: Optional[str] = None
    description: Optional[str] = None
    type_hint: Optional[str] = None
    default_value: Optional[Any] = None
    value: Optional[Any] = None
    required: Optional[bool] = None

    class Config:
        extra = "allow"

class StrategyCreate(BaseModel):
    strategy_id: str
    name: str
    version: Optional[str] = None
    vendor: Optional[str] = None
    source_ref: Optional[str] = None
    notes: Optional[str] = None
    parameters_json: List[StrategyParameter] = Field(default_factory=list)

class StrategyInstanceCreate(BaseModel):
    instance_id: str
    strategy_id: str
    instance_name: Optional[str] = None
    parameters_json: Dict[str, Any]
    symbol: Optional[str] = None
    symbols_json: Optional[List[str]] = None
    timeframe: Optional[str] = None
    account_id: Optional[str] = None
    venue: Optional[str] = None

class StrategyRunCreate(BaseModel):
    run_id: str
    instance_id: str
    run_type: str # BACKTEST, LIVE, etc.
    start_utc: datetime
    status: str = "RUNNING"
    engine_version: Optional[str] = None
    data_source: Optional[str] = None
    initial_balance: Optional[float] = None
    base_currency: Optional[str] = None
    metrics_json: Optional[Dict[str, Any]] = None

class IngestStrategySeed(BaseModel):
    strategy_id: Optional[str] = None
    name: str
    version: Optional[str] = None
    vendor: Optional[str] = None
    source_ref: Optional[str] = None
    notes: Optional[str] = None
    parameters_json: List[StrategyParameter] = Field(default_factory=list)

class IngestInstanceSeed(BaseModel):
    instance_id: Optional[str] = None
    instance_name: Optional[str] = None
    parameters_json: Dict[str, Any] = Field(default_factory=dict)
    symbol: Optional[str] = None
    symbols_json: Optional[List[str]] = None
    timeframe: Optional[str] = None
    account_id: Optional[str] = None
    venue: Optional[str] = None

class IngestRunSeed(BaseModel):
    run_type: str = "LIVE"
    start_utc: Optional[datetime] = None
    engine_version: Optional[str] = None
    data_source: Optional[str] = None
    initial_balance: Optional[float] = None
    base_currency: Optional[str] = None
    metrics_json: Optional[Dict[str, Any]] = None

class IngestRunStartRequest(BaseModel):
    strategy: IngestStrategySeed
    instance: IngestInstanceSeed
    run: IngestRunSeed

class IngestRunStartResponse(BaseModel):
    strategy_id: str
    instance_id: str
    run_id: str
    run_type: str
    start_utc: datetime
    status: str

class StartRunRequest(BaseModel):
    strategy_id: str
    parameters: Dict[str, Any] = {}
    data_range: Optional[Dict[str, Any]] = None
    run_type: Optional[str] = "BACKTEST"


class StrategyRunUpdate(BaseModel):
    status: Optional[str] = None
    end_utc: Optional[datetime] = None
    metrics_json: Optional[Dict[str, Any]] = None

class OrderCreate(BaseModel):
    run_id: str
    order_id: str
    strategy_id: Optional[str] = None # Optional redundancy
    parent_order_id: Optional[str] = None
    symbol: str
    account_id: Optional[str] = None
    side: Side
    order_type: OrderType
    time_in_force: Optional[str] = None
    quantity: float
    price: Optional[float] = None
    stop_price: Optional[float] = None
    status: OrderStatus
    submit_utc: datetime
    client_tag: Optional[str] = None
    position_impact: Optional[PositionImpactType] = PositionImpactType.UNKNOWN
    extra_json: Optional[Dict[str, Any]] = None

class OrderUpdate(BaseModel):
    status: OrderStatus
    update_utc: datetime
    # Add other fields that can change (e.g. quantity filled logic handled elsewhere?)
    
class ExecutionCreate(BaseModel):
    run_id: str
    execution_id: str
    order_id: str
    exec_utc: datetime
    price: float
    quantity: float
    fee: Optional[float] = 0.0
    fee_currency: Optional[str] = None
    liquidity: Optional[str] = None
    position_impact: Optional[PositionImpactType] = PositionImpactType.UNKNOWN
    extra_json: Optional[Dict[str, Any]] = None

class BarCreate(BaseModel):
    run_id: str
    symbol: str
    timeframe: str
    venue: Optional[str] = "Unknown"
    provider: Optional[str] = "Unknown"
    ts_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    volumetric_json: Optional[Dict[str, Any]] = None

class StreamIngestRequest(BaseModel):
    orders: Optional[List[OrderCreate]] = []
    executions: Optional[List[ExecutionCreate]] = []

class ConnectionCreate(BaseModel):
    connection_id: Optional[str] = None
    user_id: Optional[str] = None
    name: Optional[str] = None
    platform: str
    mode: ConnectionMode = ConnectionMode.LIVE
    status: ConnectionStatus = ConnectionStatus.PENDING
    account_id: Optional[str] = None
    capabilities_json: Optional[Dict[str, Any]] = None
    config_json: Optional[Dict[str, Any]] = None
    secrets_json: Optional[Dict[str, Any]] = None
    meta_json: Optional[Dict[str, Any]] = None

class ConnectionUpdate(BaseModel):
    name: Optional[str] = None
    platform: Optional[str] = None
    mode: Optional[ConnectionMode] = None
    status: Optional[ConnectionStatus] = None
    account_id: Optional[str] = None
    capabilities_json: Optional[Dict[str, Any]] = None
    config_json: Optional[Dict[str, Any]] = None
    secrets_json: Optional[Dict[str, Any]] = None
    meta_json: Optional[Dict[str, Any]] = None

class ConnectionHeartbeat(BaseModel):
    heartbeat_utc: Optional[datetime] = None
    status: Optional[ConnectionStatus] = None
    latency_ms: Optional[float] = None


# --- Response Schemas (Read) ---

class StrategyResponse(StrategyCreate):
    created_utc: datetime
    class Config:
        from_attributes = True

class StrategyInstanceResponse(StrategyInstanceCreate):
    created_utc: datetime
    class Config:
        from_attributes = True

class StrategyRunResponse(StrategyRunCreate):
    end_utc: Optional[datetime] = None
    created_utc: datetime
    class Config:
        from_attributes = True

class OrderResponse(OrderCreate):
    id: int
    class Config:
        from_attributes = True

class ExecutionResponse(ExecutionCreate):
    id: int
    class Config:
        from_attributes = True

class BarResponse(BaseModel):
    ts_utc: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    class Config:
        from_attributes = True

class ConnectionResponse(BaseModel):
    connection_id: str
    user_id: Optional[str] = None
    name: Optional[str] = None
    platform: str
    mode: ConnectionMode
    status: ConnectionStatus
    account_id: Optional[str] = None
    capabilities_json: Optional[Dict[str, Any]] = None
    config_json: Optional[Dict[str, Any]] = None
    meta_json: Optional[Dict[str, Any]] = None
    created_utc: datetime
    updated_utc: datetime
    last_heartbeat_utc: Optional[datetime] = None
    last_latency_ms: Optional[float] = None

    class Config:
        from_attributes = True
