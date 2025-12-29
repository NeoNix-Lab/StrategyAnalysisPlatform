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
                keras_layer_def = layer_conf.get('layer', {})
                l_type = keras_layer_def.get('type')
                config = keras_layer_def.get('params', {})
                
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
