from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum

# Enums
class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"

class OrderStatus(str, Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

# Base Models
class BarBase(BaseModel):
    symbol: str
    timeframe: str
    timestamp: datetime
    end_time: Optional[datetime] = None
    open: float
    high: float
    low: float
    close: float
    volume: float
    open_interest: Optional[float] = None

class OrderBase(BaseModel):
    order_id: str
    parent_order_id: Optional[str] = None
    strategy_id: str
    strategy_version: Optional[str] = None
    account_id: str
    symbol: str
    side: Side
    order_type: OrderType
    time_in_force: Optional[str] = "GTC"
    submit_time: datetime
    price: Optional[float] = None
    stop_price: Optional[float] = None
    quantity: float
    status: OrderStatus
    reject_reason: Optional[str] = None
    cancel_reason: Optional[str] = None
    client_tag: Optional[str] = None
    meta_json: Optional[str] = None

class ExecutionBase(BaseModel):
    execution_id: str
    order_id: str
    strategy_id: Optional[str] = None
    account_id: Optional[str] = None
    symbol: str
    side: Side
    exec_time: datetime
    price: float
    quantity: float
    fee: float = 0.0
    fee_currency: Optional[str] = None
    liquidity_flag: Optional[str] = None

# Create Models (Input)
class BarCreate(BarBase):
    pass

class OrderCreate(OrderBase):
    pass

class ExecutionCreate(ExecutionBase):
    pass

# Response Models
class BarResponse(BarBase):
    class Config:
        from_attributes = True

class OrderResponse(OrderBase):
    class Config:
        from_attributes = True

class ExecutionResponse(ExecutionBase):
    class Config:
        from_attributes = True
