# Data Conversion for ML Training

This module provides comprehensive data conversion capabilities for ML training datasets, supporting multiple file formats and seamless integration with the existing training pipeline.

## Supported Formats

- **CSV** - Comma-separated values with auto-detection of numeric columns
- **JSON** - Both array of objects and nested structures
- **SQL/SQLite** - Direct database queries and table imports

## API Endpoints

### Upload File to Existing Dataset
```
POST /api/datasets/{dataset_id}/upload-file
Content-Type: multipart/form-data

Parameters:
- file: The data file (CSV, JSON, SQL)
- config: JSON string with conversion configuration (optional)
```

### Create Dataset and Upload File
```
POST /api/datasets/upload-file-create
Content-Type: multipart/form-data

Parameters:
- name: Dataset name
- description: Dataset description (optional)
- file: The data file
- config: JSON string with conversion configuration (optional)
```

## Configuration Examples

### CSV Configuration
```json
{
  "format": "csv",
  "csv_config": {
    "timestamp_column": "datetime",
    "feature_columns": ["open", "high", "low", "close", "volume"],
    "target_columns": ["next_return"],
    "group_column": "symbol"
  }
}
```

### JSON Configuration
```json
{
  "format": "json",
  "json_config": {
    "timestamp_field": "ts",
    "features_field": "features",
    "targets_field": "labels",
    "group_field": "episode"
  }
}
```

### SQLite Configuration
```json
{
  "format": "sqlite",
  "sql_config": {
    "table_name": "market_data",
    "timestamp_column": "timestamp",
    "feature_columns": ["price", "volume", "bid", "ask"],
    "target_columns": ["direction"],
    "group_column": "instrument"
  }
}
```

## Training Integration

The training runner now supports three data sources:

### 1. Direct Raw Data (Legacy)
```python
config = {
    "data": [
        {"close": 100, "open": 99, "high": 101, "low": 98, "volume": 1000},
        # ... more rows
    ],
    "training_params": {...}
}
```

### 2. Dataset from Database
```python
config = {
    "dataset_id": "uuid-of-dataset",
    "training_params": {...}
}
```

### 3. File Upload
```python
config = {
    "file_path": "/path/to/data.csv",
    "file_config": {
        "format": "csv",
        "csv_config": {
            "timestamp_column": "date",
            "feature_columns": ["price", "volume"]
        }
    },
    "training_params": {...}
}
```

## Data Flow

1. **Upload** → File uploaded via API endpoint
2. **Convert** → DataConverter transforms to MlDatasetSample format
3. **Validate** → Schema validation and error checking
4. **Store** → Bulk insert into database
5. **Train** → Training Runner loads and processes for ML

## Auto-Detection Features

- **CSV**: Automatically detects numeric columns as features if not specified
- **JSON**: Supports multiple JSON structures (array, nested, single object)
- **SQL**: Can infer table structure or use custom queries

## Error Handling

- File format validation
- Schema validation with detailed error messages
- Transaction rollback on errors
- Temporary file cleanup
- Comprehensive logging

## Usage Examples

### Upload CSV with Auto-Detection
```bash
curl -X POST "http://localhost:8000/api/datasets/upload-file-create" \
  -F "name=Market Data" \
  -F "file=@market_data.csv" \
  -F 'config={"format": "csv", "csv_config": {"timestamp_column": "date"}}'
```

### Upload JSON with Custom Structure
```bash
curl -X POST "http://localhost:8000/api/datasets/upload-file-create" \
  -F "name=Training Data" \
  -F "file=@training_data.json" \
  -F 'config={"format": "json", "json_config": {"features_field": "input", "targets_field": "output"}}'
```

### Training with File Data
```python
training_config = {
    "file_path": "/data/training_set.csv",
    "file_config": {
        "format": "csv",
        "csv_config": {
            "feature_columns": ["feature1", "feature2", "feature3"],
            "target_columns": ["target"]
        }
    },
    "training_params": {
        "epochs": 10,
        "batch_size": 32,
        "learning_rate": 0.001
    }
}
```
