from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from ..common.models import RunType, RunStatus

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

class Strategy(BaseModel):
    strategy_id: str
    name: str
    version: Optional[str] = None
    vendor: Optional[str] = None
    source_ref: Optional[str] = None
    created_utc: datetime
    notes: Optional[str] = None
    parameters_json: List[StrategyParameter] = Field(default_factory=list)

class StrategyInstance(BaseModel):
    instance_id: str
    strategy_id: str
    instance_name: Optional[str] = None
    parameters_json: Dict[str, Any]
    symbols_json: List[str]
    timeframe: Optional[str] = None
    account_id: Optional[str] = None
    venue: Optional[str] = None
    created_utc: datetime

class StrategyRun(BaseModel):
    run_id: str
    instance_id: str
    run_type: RunType
    start_utc: datetime
    end_utc: Optional[datetime] = None
    status: RunStatus
    engine_version: Optional[str] = None
    data_source: Optional[str] = None
    initial_balance: Optional[float] = None
    base_currency: Optional[str] = None
    metrics_json: Optional[Dict[str, Any]] = None
    created_utc: datetime
