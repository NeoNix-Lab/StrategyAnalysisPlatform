from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any

class Dataset(BaseModel):
    dataset_id: str
    name: str
    description: Optional[str] = None
    created_utc: datetime
    sources_json: List[Dict[str, Any]]
    feature_config_json: Optional[List[str]] = None
