
import pandas as pd
import json
import numpy as np
from typing import List, Dict, Any, Callable
from sqlalchemy.orm import Session
from src.database.models import Dataset, Bar, RunSeries, MlRewardFunction, MarketSeries, MarketBar

# Try importing tensorflow, but don't crash if missing (allows server to list files etc)
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras import layers
except ImportError:
    tf = None
    keras = None
    layers = None

def load_dataset_as_dataframe(db: Session, dataset_id: str) -> pd.DataFrame:
    """
    Reconstructs a Pandas DataFrame for a given Dataset ID.
    Fetches bars from all source runs defined in sources_json.
    """
    dataset = db.query(Dataset).get(dataset_id)
    if not dataset:
        raise ValueError(f"Dataset {dataset_id} not found")
        
    sources = dataset.sources_json
    if not sources:
        raise ValueError("Dataset has no sources defined")

    all_dfs = []
    
    for source in sources:
        run_id = source.get("run_id")
        symbol = source.get("symbol")
        timeframe = source.get("timeframe")
        
        # Strategy 1: Context is a Strategy Run
        bars_found = []
        
        if run_id:
            series_query = db.query(RunSeries).filter(RunSeries.run_id == run_id)
            if symbol: series_query = series_query.filter(RunSeries.symbol == symbol)
            if timeframe: series_query = series_query.filter(RunSeries.timeframe == timeframe)
            
            series_list = series_query.all()
            if series_list:
                for s in series_list:
                    b_list = db.query(Bar).filter(Bar.series_id == s.series_id).order_by(Bar.ts_utc).all()
                    if b_list: 
                        bars_found.extend(b_list)
                        break # Assume we want the first matching series for this source entry
        
        # Strategy 2: Context is Market Data (Fallback if no Run data found)
        if not bars_found and symbol and timeframe:
             m_series = db.query(MarketSeries).filter(
                 MarketSeries.symbol == symbol,
                 MarketSeries.timeframe == timeframe
             ).first()
             
             if m_series:
                 bars_found = db.query(MarketBar).filter(MarketBar.series_id == m_series.series_id).order_by(MarketBar.ts_utc).all()

        if not bars_found:
            continue
            
        # Convert to Dict
        data = []
        for b in bars_found:
            row = {
                "ts_utc": b.ts_utc,
                "open": b.open,
                "high": b.high,
                "low": b.low,
                "close": b.close,
                "volume": b.volume
            }
            data.append(row)
            
        df = pd.DataFrame(data)
        all_dfs.append(df)
        
    if not all_dfs:
        raise ValueError("No data found for the given dataset sources")
        
    # Concatenate all runs (assuming they are sequential segments or we simple append them)
    # If they are parallel (different assets), logic would be different.
    # For MVP: Vertical concatenation (Time extension).
    final_df = pd.concat(all_dfs, ignore_index=True)
    final_df.sort_values("ts_utc", inplace=True)
    final_df.reset_index(drop=True, inplace=True)
    
    return final_df

def build_keras_model(layers_config: List[Dict[str, Any]], input_shape: tuple) -> Any:
    """
    Builds a Keras model from a JSON list of layer configurations.
    Example config: [{"type": "Dense", "units": 64, "activation": "relu"}, ...]
    """
    if not tf:
        raise ImportError("TensorFlow is not installed.")

    model = keras.Sequential()
    model.add(layers.InputLayer(input_shape=input_shape))

    for layer_cfg in layers_config:
        l_type = layer_cfg.get("type")
        params = layer_cfg.copy()
        if "type" in params: del params["type"]
        
        if l_type == "Dense":
            model.add(layers.Dense(**params))
        elif l_type == "LSTM":
            model.add(layers.LSTM(**params))
        elif l_type == "Dropout":
            model.add(layers.Dropout(**params))
        elif l_type == "Flatten":
            model.add(layers.Flatten(**params))
        else:
            # Fallback for generic layers if available in keras.layers
            if hasattr(layers, l_type):
                layer_class = getattr(layers, l_type)
                model.add(layer_class(**params))
            else:
                raise ValueError(f"Unknown layer type: {l_type}")

    # Output layer for Actions (3 actions: Wait, Long, Short)
    # We implicitly add this if not present? Or expect it in config?
    # For safety, let's assume the config covers the hidden layers, and we might strictly enforce the output size
    # But usually the architecture should define it.
    # If the last layer units != 3, we might have a problem for this specific env.
    
    return model

def get_reward_function(db: Session, function_id: str) -> Callable:
    """
    Loads and parses the reward function code.
    Returns a callable: func(env, action)
    """
    rf_record = db.query(MlRewardFunction).get(function_id)
    if not rf_record:
        raise ValueError(f"Reward Function {function_id} not found")
        
    code_snippet = rf_record.code
    
    # Secure(ish) execution namespace
    # We expect the code to define a function named 'calculate_reward(env, action)'
    local_scope = {}
    
    # Basic imports available to the snippet
    global_scope = {
        "np": np,
        "pd": pd
    }
    
    try:
        exec(code_snippet, global_scope, local_scope)
    except Exception as e:
        raise ValueError(f"Error parsing reward function code: {e}")
        
    if "calculate_reward" not in local_scope:
        raise ValueError("The reward function code must define 'def calculate_reward(env, action):'")
        
    return local_scope["calculate_reward"]
