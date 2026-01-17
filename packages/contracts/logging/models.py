from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any

class LogRecord(BaseModel):
    """
    Standardized log record structure for the entire platform.
    Acts as the Single Source of Truth for log data exchange.
    """
    timestamp: datetime = Field(..., description="UTC timestamp of the log event")
    level: str = Field(..., description="Log level (INFO, WARNING, ERROR, DEBUG, CRITICAL)")
    name: str = Field(..., description="Logger name (service or module)")
    message: str = Field(..., description="Log message content")
    
    # Optional metadata for structured logging (e.g. trace_id, user_id, context)
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional context metadata")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
