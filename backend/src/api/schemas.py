from pydantic import BaseModel
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

# --- Input Schemas (Create/Ingest) ---

class StrategyCreate(BaseModel):
    strategy_id: str
    name: str
    version: Optional[str] = None
    vendor: Optional[str] = None
    source_ref: Optional[str] = None
    notes: Optional[str] = None

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
