"""
Configuration examples and validation schemas for data conversion
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Any, Optional, Union
from enum import Enum

class FileFormat(str, Enum):
    CSV = "csv"
    JSON = "json"
    SQL = "sql"
    SQLITE = "sqlite"

class CSVConfig(BaseModel):
    """Configuration for CSV file conversion"""
    timestamp_column: Optional[str] = Field(None, description="Column name for timestamps")
    feature_columns: Optional[List[str]] = Field(None, description="List of feature column names")
    target_columns: Optional[List[str]] = Field(None, description="List of target column names")
    group_column: Optional[str] = Field(None, description="Column name for grouping")
    
    @validator('feature_columns')
    def validate_features(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError("feature_columns cannot be empty when specified")
        return v

class JSONConfig(BaseModel):
    """Configuration for JSON file conversion"""
    timestamp_field: Optional[str] = Field("timestamp", description="Field name for timestamps")
    features_field: Optional[str] = Field("features", description="Field name for features")
    targets_field: Optional[str] = Field("targets", description="Field name for targets")
    group_field: Optional[str] = Field("group_id", description="Field name for grouping")

class SQLConfig(BaseModel):
    """Configuration for SQL/SQLite file conversion"""
    table_name: Optional[str] = Field(None, description="Table name to query")
    query: Optional[str] = Field(None, description="Custom SQL query")
    timestamp_column: Optional[str] = Field(None, description="Column name for timestamps")
    feature_columns: Optional[List[str]] = Field(None, description="List of feature column names")
    target_columns: Optional[List[str]] = Field(None, description="List of target column names")
    group_column: Optional[str] = Field(None, description="Column name for grouping")
    
    @validator('query')
    def validate_query_or_table(cls, v, values):
        if v is None and values.get('table_name') is None:
            raise ValueError("Either query or table_name must be specified")
        return v

class DataConversionConfig(BaseModel):
    """Main configuration for data conversion"""
    format: FileFormat
    csv_config: Optional[CSVConfig] = None
    json_config: Optional[JSONConfig] = None
    sql_config: Optional[SQLConfig] = None
    
    @validator('csv_config')
    def validate_csv_config(cls, v, values):
        if values.get('format') == FileFormat.CSV and v is None:
            raise ValueError("csv_config is required for CSV format")
        return v
    
    @validator('json_config')
    def validate_json_config(cls, v, values):
        if values.get('format') == FileFormat.JSON and v is None:
            raise ValueError("json_config is required for JSON format")
        return v
    
    @validator('sql_config')
    def validate_sql_config(cls, v, values):
        if values.get('format') in [FileFormat.SQL, FileFormat.SQLITE] and v is None:
            raise ValueError("sql_config is required for SQL/SQLite format")
        return v

# Example configurations
EXAMPLE_CONFIGS = {
    "csv_example": {
        "format": "csv",
        "csv_config": {
            "timestamp_column": "datetime",
            "feature_columns": ["open", "high", "low", "close", "volume"],
            "target_columns": ["next_return"],
            "group_column": "symbol"
        }
    },
    
    "json_example": {
        "format": "json",
        "json_config": {
            "timestamp_field": "ts",
            "features_field": "features",
            "targets_field": "labels",
            "group_field": "episode"
        }
    },
    
    "sqlite_example": {
        "format": "sqlite",
        "sql_config": {
            "table_name": "market_data",
            "timestamp_column": "timestamp",
            "feature_columns": ["price", "volume", "bid", "ask"],
            "target_columns": ["direction"],
            "group_column": "instrument"
        }
    },
    
    "csv_auto_detect": {
        "format": "csv",
        "csv_config": {
            "timestamp_column": "date",
            # feature_columns will be auto-detected as all numeric columns
            "target_columns": ["target"]
        }
    }
}

def get_example_config(format_type: str) -> Dict[str, Any]:
    """Get example configuration for a specific format"""
    key = f"{format_type}_example"
    if key in EXAMPLE_CONFIGS:
        return EXAMPLE_CONFIGS[key]
    return EXAMPLE_CONFIGS["csv_auto_detect"]

def validate_config(config: Dict[str, Any]) -> DataConversionConfig:
    """Validate and parse configuration"""
    return DataConversionConfig(**config)
