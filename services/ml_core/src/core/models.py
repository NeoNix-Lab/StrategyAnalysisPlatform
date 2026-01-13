from enum import Enum
import json
import tensorflow as tf
from tensorflow import keras as k
from typing import List, Dict, Any, Union, Tuple

class LayersType(Enum):
    """
    Enumeration for identifying the type of a neural network layer.
    """
    INPUT = 'input'
    HIDDEN = 'hidden'
    OUTPUT = 'output'

class CustomDQNModel(tf.keras.Model):
    """
    Custom Deep Q-Network model using Keras.
    Constructed from a configuration dictionary/list rather than a database.
    """

    def __init__(self, architecture_config: List[Dict[str, Any]], input_shape: int, name: str = "CustomDQN"):
        """
        Initialize the model from a configuration list.

        Args:
            architecture_config: List of layer configurations. 
                                 Each item should be a dict with keys: 'type', 'params', 'layer_type' (input/hidden/output).
            input_shape: Size of the sliding window input.
            name: Model name.
        """
        super().__init__(name=name)
        self.custom_name = name
        self.window_size = input_shape
        self.architecture_config = architecture_config
        self.model_layers = []
        
        # Build layers immediately upon initialization
        self.build_layers()

    def build_layers(self):
        """Constructs the internal Keras layers based on the provided configuration."""
        try:
            # 1. Ajust Input Shape
            for layer_conf in self.architecture_config:
                # We expect layer_conf to have structure like:
                # { "layer": { "type": "Dense", "params": { "units": 64, ... } }, "type": "input" }
                # Or simplified: { "type": "Dense", "params": { ... }, "meta_type": "input" }
                
                # Handling the structure from the old 'Layers' object style:
                # The old code accessed layer.layer['params']['input_shape']
                
                # Check if this is an input layer
                meta_type = layer_conf.get('type') # 'input', 'hidden', 'output' (from enum value)
                
                # The actual Keras layer config is inside 'layer' key in the old DB schema
                keras_layer_def = layer_conf.get('layer', {})
                keras_type = keras_layer_def.get('type')
                keras_params = keras_layer_def.get('params', {})

                if meta_type == LayersType.INPUT.value:
                    shape = keras_params.get('input_shape')
                    if shape and isinstance(shape, (list, tuple)):
                        shape = list(shape)
                        # Overwrite the first dimension (window size)
                        shape[0] = self.window_size
                        keras_params['input_shape'] = tuple(shape)

            # 2. Instantiate Layers
            for idx, layer_conf in enumerate(self.architecture_config):
                # Support both legacy {"layer": {"type": "Dense"}} and new {"type": "Dense"} formats
                if 'layer' in layer_conf:
                     keras_layer_def = layer_conf.get('layer', {})
                     l_type = keras_layer_def.get('type')
                     config = keras_layer_def.get('params', {})
                else:
                     l_type = layer_conf.get('type')
                     config = layer_conf.copy()
                     if 'type' in config:
                         del config['type']
                
                # If meta_type is input, we might have stored params in config. 
                # But typically 'params' is not top level in new format unless we standardize.
                # Actually, the frontend stores params directly as keys e.g. {type: Dense, units: 64}
                # So config = layer_conf without 'type' is correct for flat format.
                
                # Ensure unique names
                if 'name' not in config:
                    config['name'] = f'{l_type}_{idx}'
                
                if hasattr(tf.keras.layers, l_type):
                    layer_class = getattr(tf.keras.layers, l_type)
                    layer = layer_class(**config)
                    self.model_layers.append(layer)
                else:
                    print(f"Warning: Unknown layer type {l_type}")

        except Exception as e:
            raise ValueError(f"Error while building layers: {e}")

    def call(self, inputs, training=None):
        """Forward pass for the model."""
        x = inputs
        for layer in self.model_layers:
            x = layer(x)
        return x

    def get_config(self):
        return {
            "name": self.custom_name,
            "input_shape": self.window_size,
            "architecture_config": self.architecture_config
        }

    @classmethod
    def from_config(cls, config):
        return cls(**config)

    def extract_standard_keras_model(self, shape=None):
        """
        Build a standard Keras Functional Model object from internal layers.
        This ensures compatibility with standard Keras training loops and serialization.
        
        Args:
            shape: Input shape (optional). If None, uses a placeholder shape based on window_size.
        """
        try:
            if shape is None:
                # Default placeholder shape if not provided (batch_size, window_size, features)
                # We assume a feature dimension of 5 (OHLCV) or inferred from usage if possible.
                # However, usually this is called with a concrete tensor sample.
                shape = (self.window_size, 5) 
            
            # If shape is a Tensor/Array, extract shape tuple
            if hasattr(shape, 'shape'):
                input_shape = shape.shape
                # If first dim is batch (often None or discrete), we need the feature info.
                # Keras Input expects shape=(features,) or (time_steps, features).
                # If input_shape is (32, 10, 5), we want (10, 5).
                if len(input_shape) > 1:
                     input_shape = input_shape[1:]
            elif isinstance(shape, (tuple, list)):
                 input_shape = shape
            else:
                 input_shape = (self.window_size, 5)

            x = k.Input(shape=input_shape)
            out = x
            for layer in self.model_layers:
                out = layer(out)
            
            # Create standard functional model
            standard_model = k.Model(inputs=x, outputs=out, name=self.custom_name)
            return standard_model
            
        except Exception as e:
            print(f"Error generating standard Keras model: {e}")
            raise e
