from pydantic import BaseModel, Field, Generic
from typing import Optional, Dict, Any, TypeVar
from datetime import datetime
import uuid

T = TypeVar('T')

class TraceableRequest(BaseModel):
    """
    Base model for all requests that require tracing.
    """
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique request ID for distributed tracing")
    client_id: Optional[str] = Field(None, description="Client identifier (e.g. frontend-v1)")

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Dict[str, Any]] = None

class EnvelopedResponse(BaseModel, Generic[T]):
    """
    Standard response envelope for all API endpoints.
    """
    data: Optional[T] = None
    trace_id: str = Field(..., description="Trace ID tied to the request")
    status: str = Field("success", description="Response status: success, error")
    error: Optional[ErrorDetail] = None
    meta: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Metadata like pagination, timing, etc.")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
