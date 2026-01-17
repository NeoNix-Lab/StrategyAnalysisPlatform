# -*- coding: utf-8 -*-
"""
Utility functions for retrieving and constructing core objects from the database.
"""
from ..service.db_manager import DBManager
from ..models.dati import Dati
from ..models.training_model import Training_Model
from ..models.model_static import CustomDQNModel, Layers
from ..models.iteration import Iterazione
from ..models.reward_function import RewardFunction as Rewar_Function
from ..models.process import Process
import tensorflow as tf
import pandas as pd
from typing import Any, Callable, List, Tuple, Dict, Optional

dbmanager = DBManager("C:\\Users\\user\\OneDrive\\Desktop\\DB\\RNN_Tuning_V01.db")


# Map table names to their corresponding classes
object_mapping: Dict[str, Any] = {
    'dati': Dati,
    'training': Training_Model,
    'models': CustomDQNModel,
    'layers': Layers,
    'iterazioni': Iterazione,
    'functions': Rewar_Function,
    'processes': Process
}


def retrieve_generic_obj(obj_type: str) -> Tuple[List[Any], List[str], List[int], Optional[str]]:
    """
    Retrieve and instantiate all records of a given type from the database.

    Args:
        obj_type (str): Key of the object to retrieve (e.g. 'dati', 'training').

    Returns:
        Tuple containing:
          - list of instantiated objects
          - list of object names (if .name attribute exists)
          - list of object IDs
          - error message or None
    """
    cls = object_mapping.get(obj_type.lower())
    if cls is None:
        return [], [], [], f"Unknown object type: {obj_type}"

    try:
        rows = dbmanager.retrieve_all(obj_type)
    except Exception as e:
        return [], [], [], str(e)

    instances, names, ids = [], [], []
    for row in rows:
        try:
            obj = cls.convert_db_response(row)
            instances.append(obj)
            names.append(getattr(obj, 'name', None))
            ids.append(getattr(obj, 'id', None))
        except Exception:
            continue
    return instances, names, ids, None


def sort_layers_by_index(relations: List[Tuple[int, int, int]]) -> List[int]:
    """
    Sort records of (model_id, layer_id, layer_index) by layer_index.

    Args:
        relations: list of tuples from model_layer_relation table.

    Returns:
        Ordered list of layer IDs.
    """
    sorted_rel = sorted(relations, key=lambda r: r[2])
    return [r[1] for r in sorted_rel]


def build_static_model_from_id(model_id: int, input_shape: int) -> CustomDQNModel:
    """
    Reconstruct a CustomDQNModel from the database by its ID.

    Args:
        model_id (int): ID of the model in the 'models' table.
        input_shape (int): Window size or input dimension for the model.

    Returns:
        CustomDQNModel: Instantiated model with layers loaded.

    Raises:
        ValueError: If the model or its layers cannot be retrieved.
    """
    # Fetch raw model record
    rows = dbmanager.retrieve_list_of_records('id', 'models', [model_id])
    if not rows:
        raise ValueError(f"Model with id {model_id} not found.")
    model_row = rows[0]

    # Fetch and sort layer relations
    rels = dbmanager.retrieve_list_of_records('id_model', 'model_layer_relation', [model_id])
    layer_ids = sort_layers_by_index(rels)

    # Fetch layer definitions
    layer_rows = dbmanager.retrieve_list_of_records('id', 'layers', layer_ids)
    layer_objs = [Layers.convert_db_response(r) for r in layer_rows]

    # Instantiate the model (no DB push)
    # model_row format: (id, model_json, name, note)
    name = model_row[2] if len(model_row) > 2 else f"model_{model_id}"
    return CustomDQNModel(layer_objs, input_shape, name=name, id=model_id, push=False)


def build_and_test_environment(
        data: pd.DataFrame,
        reward_fn: Callable[[Any, int], float],
        action_labels: List[str],
        window_size: int,
        feature_columns: Optional[List[str]] = None,
        test_action: int = 0
) -> Tuple[Any, pd.DataFrame]:
    """
    Build an EnvFlex environment, run a single test step, and return results.

    Args:
        data (pd.DataFrame): Time-series DataFrame.
        reward_fn: Injected reward function.
        action_labels: List of discrete action labels.
        window_size: Number of timesteps per observation.
        feature_columns: Columns to use; defaults to all.
        test_action: Action index to apply in the first step.

    Returns:
        Tuple of (env instance, observation DataFrame).
    """
    env = EnvFlex(
        data=data,
        window_size=window_size,
        reward_fn=reward_fn,
        action_labels=action_labels,
        feature_columns=feature_columns
    )
    obs, reward, done, info = env.step(test_action)
    # Convert original DataFrame window back for inspection
    obs_df = pd.DataFrame(obs, columns=feature_columns or data.columns.tolist())
    return env, obs_df



def load_keras_model_from_db(model_id: int) -> tf.keras.Model:
    """
    Load a pure Keras model from the 'models' table by its ID.

    Assumes the 'models' table stores the model architecture as JSON in the
    second column, in this schema: (id, model_json, name, note).

    Args:
        model_id (int): Primary key of the model in the 'models' table.

    Returns:
        tf.keras.Model: Reconstructed Keras model (uncompiled).
    """
    # recupera la riga (id, model_json, name, note)
    row = dbmanager.retrieve_item('models', 'id', model_id)
    if row is None:
        raise ValueError(f"Model with id={model_id} not found in DB.")
    model_json = row[1]
    model = tf.keras.models.model_from_json(model_json)
    return model

def load_compiled_model_from_db(model_id: int, weights_path: str, optimizer, loss) -> tf.keras.Model:
    model = load_keras_model_from_db(model_id)
    model.compile(optimizer=optimizer, loss=loss)
    model.load_weights(weights_path)
    return model


