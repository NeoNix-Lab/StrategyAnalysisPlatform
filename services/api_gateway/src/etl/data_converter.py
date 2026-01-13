"""
Data Conversion Module for ML Datasets
Supports conversion from CSV, JSON, SQL to MlDatasetSample format
"""

import pandas as pd
import sqlite3
import json
import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import numpy as np

logger = logging.getLogger(__name__)

class DataConverter:
    """
    Converts external data sources (CSV, JSON, SQL) to MlDatasetSample format
    """
    
    def __init__(self):
        self.supported_formats = ['csv', 'json', 'sql', 'sqlite']
    
    def convert_from_file(self, file_path: Union[str, Path], 
                         config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Main entry point - converts file to list of MlDatasetSample dictionaries
        
        Args:
            file_path: Path to the data file
            config: Conversion configuration
            
        Returns:
            List of dictionaries ready for MlDatasetSample insertion
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = file_path.suffix.lower().lstrip('.')
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported format: {file_ext}. Supported: {self.supported_formats}")
        
        config = config or {}
        limit = config.get('limit')
        
        if file_ext == 'csv':
            return self._convert_csv(file_path, config, limit)
        elif file_ext == 'json':
            return self._convert_json(file_path, config, limit)
        elif file_ext in ['sql', 'sqlite']:
            return self._convert_sqlite(file_path, config, limit)
    
    def _convert_csv(self, file_path: Path, config: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Convert CSV file to MlDatasetSample format"""
        try:
            # Read CSV with pandas
            df = pd.read_csv(file_path, nrows=limit)
            
            # Configuration options
            timestamp_col = config.get('timestamp_column')
            feature_columns = config.get('feature_columns', [])
            target_columns = config.get('target_columns', [])
            group_column = config.get('group_column')
            
            # Auto-detect columns if not specified
            if not feature_columns:
                # Use all numeric columns except timestamp and targets as features
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                feature_columns = [col for col in numeric_cols 
                                 if col not in (target_columns + [timestamp_col])]
            
            samples = []
            for idx, row in df.iterrows():
                # Extract timestamp
                timestamp = None
                if timestamp_col and timestamp_col in row:
                    timestamp = pd.to_datetime(row[timestamp_col]).to_pydatetime()
                
                # Extract features
                features = {}
                for col in feature_columns:
                    if col in row:
                        features[col] = self._convert_value(row[col])
                
                # Extract targets
                targets = None
                if target_columns:
                    targets = {}
                    for col in target_columns:
                        if col in row:
                            targets[col] = self._convert_value(row[col])
                
                # Extract group ID
                group_id = None
                if group_column and group_column in row:
                    group_id = str(row[group_column])
                
                sample = {
                    'timestamp_utc': timestamp,
                    'group_id': group_id,
                    'step_index': idx,
                    'features_json': features,
                    'targets_json': targets
                }
                samples.append(sample)
            
            logger.info(f"Converted {len(samples)} samples from CSV: {file_path}")
            return samples
            
        except Exception as e:
            logger.error(f"Error converting CSV {file_path}: {e}")
            raise
    

    
    def _convert_json(self, file_path: Path, config: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Convert JSON file to MlDatasetSample format"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Handle different JSON structures
            if isinstance(data, list):
                # Array of objects
                records = data
            elif isinstance(data, dict):
                if 'data' in data:
                    records = data['data']
                elif 'samples' in data:
                    records = data['samples']
                else:
                    # Single object, wrap in list
                    records = [data]
            else:
                raise ValueError("Invalid JSON structure")
            
            samples = []
            timestamp_field = config.get('timestamp_field', 'timestamp')
            features_field = config.get('features_field', 'features')
            targets_field = config.get('targets_field', 'targets')
            group_field = config.get('group_field', 'group_id')
            
            for idx, record in enumerate(records):
                if limit and idx >= limit:
                    break
                    
                # Extract timestamp
                timestamp = None
                if timestamp_field in record:
                    timestamp = pd.to_datetime(record[timestamp_field]).to_pydatetime()
                
                # Extract features
                features = record.get(features_field, {})
                if not isinstance(features, dict):
                    # If features is not a dict, try to convert
                    if isinstance(features, (list, tuple)):
                        features = {f'feature_{i}': val for i, val in enumerate(features)}
                    else:
                        features = {'value': features}
                
                # Convert all feature values
                features = {k: self._convert_value(v) for k, v in features.items()}
                
                # Extract targets
                targets = None
                if targets_field in record:
                    targets = record[targets_field]
                    if not isinstance(targets, dict):
                        targets = {'target': self._convert_value(targets)}
                    else:
                        targets = {k: self._convert_value(v) for k, v in targets.items()}
                
                # Extract group ID
                group_id = record.get(group_field) if group_field else None
                
                sample = {
                    'timestamp_utc': timestamp,
                    'group_id': str(group_id) if group_id else None,
                    'step_index': idx,
                    'features_json': features,
                    'targets_json': targets
                }
                samples.append(sample)
            
            logger.info(f"Converted {len(samples)} samples from JSON: {file_path}")
            return samples
            
        except Exception as e:
            logger.error(f"Error converting JSON {file_path}: {e}")
            raise
    

    
    def _convert_sqlite(self, file_path: Path, config: Dict[str, Any], limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Convert SQLite database to MlDatasetSample format"""
        try:
            table_name = config.get('table_name')
            query = config.get('query')
            
            if not table_name and not query:
                raise ValueError("Either 'table_name' or 'query' must be specified in config")
            
            conn = sqlite3.connect(str(file_path))
            
            if query:
                if limit and "LIMIT" not in query.upper():
                    query += f" LIMIT {limit}"
                df = pd.read_sql_query(query, conn)
            else:
                # read_sql_table does not support limit directly in pandas < 1.4 for sqlite without sqlalchemy engine sometimes, 
                # but we usually use read_sql_query for limits. 
                # Simplest fallback: read and slice (inefficient but works for small limits) or select *
                
                query_str = f"SELECT * FROM {table_name}"
                if limit:
                    query_str += f" LIMIT {limit}"
                df = pd.read_sql_query(query_str, conn)

            
            conn.close()
            
            # Use same conversion logic as CSV
            csv_config = {
                'timestamp_column': config.get('timestamp_column'),
                'feature_columns': config.get('feature_columns', []),
                'target_columns': config.get('target_columns', []),
                'group_column': config.get('group_column')
            }
            
            # Convert DataFrame to samples
            samples = []
            timestamp_col = csv_config['timestamp_column']
            feature_columns = csv_config['feature_columns']
            target_columns = csv_config['target_columns']
            group_column = csv_config['group_column']
            
            # Auto-detect columns if not specified
            if not feature_columns:
                numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
                feature_columns = [col for col in numeric_cols 
                                 if col not in (target_columns + [timestamp_col])]
            
            for idx, row in df.iterrows():
                # Extract timestamp
                timestamp = None
                if timestamp_col and timestamp_col in row:
                    timestamp = pd.to_datetime(row[timestamp_col]).to_pydatetime()
                
                # Extract features
                features = {}
                for col in feature_columns:
                    if col in row:
                        features[col] = self._convert_value(row[col])
                
                # Extract targets
                targets = None
                if target_columns:
                    targets = {}
                    for col in target_columns:
                        if col in row:
                            targets[col] = self._convert_value(row[col])
                
                # Extract group ID
                group_id = None
                if group_column and group_column in row:
                    group_id = str(row[group_column])
                
                sample = {
                    'timestamp_utc': timestamp,
                    'group_id': group_id,
                    'step_index': idx,
                    'features_json': features,
                    'targets_json': targets
                }
                samples.append(sample)
            
            logger.info(f"Converted {len(samples)} samples from SQLite: {file_path}")
            return samples
            
        except Exception as e:
            logger.error(f"Error converting SQLite {file_path}: {e}")
            raise
    
    def get_sqlite_tables(self, file_path: Path) -> List[str]:
        """List all tables in a SQLite database"""
        try:
            conn = sqlite3.connect(str(file_path))
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            conn.close()
            return tables
        except Exception as e:
            logger.error(f"Error listing tables in {file_path}: {e}")
            raise

    def _convert_value(self, value: Any) -> Any:
        """Convert value to JSON-serializable format"""
        if pd.isna(value):
            return None
        elif isinstance(value, (np.integer, np.floating)):
            return float(value) if isinstance(value, np.floating) else int(value)
        elif isinstance(value, np.ndarray):
            return value.tolist()
        elif hasattr(value, 'item'):  # numpy scalar
            return value.item()
        else:
            return value
    
    def validate_samples(self, samples: List[Dict[str, Any]]) -> bool:
        """Validate converted samples"""
        if not samples:
            raise ValueError("No samples to validate")
        
        required_fields = ['features_json']
        optional_fields = ['timestamp_utc', 'group_id', 'step_index', 'targets_json']
        
        for i, sample in enumerate(samples):
            # Check required fields
            for field in required_fields:
                if field not in sample:
                    raise ValueError(f"Sample {i} missing required field: {field}")
            
            # Check features is dict
            if not isinstance(sample['features_json'], dict):
                raise ValueError(f"Sample {i} features_json must be a dictionary")
            
            # Check targets if present
            if sample.get('targets_json') and not isinstance(sample['targets_json'], dict):
                raise ValueError(f"Sample {i} targets_json must be a dictionary")
        
        logger.info(f"Validated {len(samples)} samples successfully")
        return True
