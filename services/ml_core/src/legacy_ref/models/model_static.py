from enum import Enum
import json
import tensorflow as tf
import keras as k

from ..service import db_manager as dbm
from .base_models import BaseModelsClass as BCM
from ..service.db_manager import DBManager


class LayersType(Enum):
    """
    Enumeration for identifying the type of a neural network layer.
    """
    INPUT = 'input'
    HIDDEN = 'hidden'
    OUTPUT = 'output'


class Layers(BCM):
    """
    Represents a neural network layer.
    Inherits from BaseModelsClass to support database persistence.
    """

    table_name = "layers"
    fields = ["layer", "name", "note", "type", "schema"]

    DB_SCHEMA = '''CREATE TABLE IF NOT EXISTS layers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        layer TEXT,
        name TEXT,
        note TEXT,
        type TEXT,
        schema TEXT
    );'''

    INSERT_QUERY = '''INSERT INTO layers (layer, name, note, type, schema)
                      VALUES (?, ?, ?, ?, ?);'''

    def __init__(self, **kwargs):
        if isinstance(kwargs.get("type"), LayersType):
            kwargs["type"] = kwargs["type"].value
        super().__init__(**kwargs)

    def to_tuple(self):
        """Serialize the layer and schema into JSON-compatible format."""
        layer_json = json.dumps(self.layer)
        schema_json = json.dumps(self.schema)
        return (layer_json, self.name, self.note, self.type, schema_json)

    @classmethod
    def convert_db_response(cls, row):
        """Convert a DB row into a Layers instance."""
        try:
            return cls(
                id=row[0],
                layer=json.loads(row[1]),
                name=row[2],
                note=row[3],
                type=LayersType(row[4]).value,
                schema=json.loads(row[5])
            )
        except Exception as e:
            raise ValueError(f"Error converting DB row to Layers: {e}")


class CustomDQNModel(tf.keras.Model):
    """
    Custom Deep Q-Network model using Keras.
    Supports serialization and persistence via database.
    """

    table_name = "models"
    fields = ["model", "name", "note"]

    DB_SCHEMA = '''CREATE TABLE IF NOT EXISTS models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        model TEXT,
        name TEXT,
        note TEXT
    );'''

    INSERT_QUERY = '''INSERT INTO models (model, name, note)
                      VALUES (?, ?, ?);'''

    DB_RELATION_SCHEMA = '''CREATE TABLE IF NOT EXISTS model_layer_relation  (
        id_model INTEGER,
        id_layer INTEGER,
        layer_index INTEGER,
        PRIMARY KEY (id_model, layer_index) ON CONFLICT IGNORE,
        FOREIGN KEY (id_model) REFERENCES models(id) ON DELETE CASCADE,
        FOREIGN KEY (id_layer) REFERENCES layers(id) ON DELETE CASCADE
    );'''

    DB_RELATION_INSERT_QUERY = '''INSERT INTO model_layer_relation (id_model, id_layer, layer_index)
                                  VALUES (?, ?, ?);'''

    def __init__(self, lay_obj, input_shape, name, push=True, id=-1):
        self.custom_name = name
        self.window_size = input_shape
        self.lay_obj = lay_obj
        self.model_layers = []
        self.layers_id = []
        self.push = push
        self.id = id
        self.set_up_layers(lay_obj)

    def build_layers(self):
        """Constructs the internal Keras layers based on the provided configuration."""
        try:
            for layer in self.lay_obj:
                if layer.type == LayersType.INPUT.value:
                    shape = layer.layer['params']['input_shape']
                    if isinstance(shape, (tuple, list)):
                        shape = list(shape)
                        shape[0] = self.window_size
                        layer.layer['params']['input_shape'] = tuple(shape)

            for idx, layer_config in enumerate(self.lay_obj):
                l_type = layer_config.layer['type']
                config = layer_config.layer['params']
                config['name'] = f'{l_type}_{idx}'
                layer = getattr(tf.keras.layers, l_type)(**config)
                self.model_layers.append(layer)

            if self.push:
                self.push_on_db(notes='Model_Compile')

        except Exception as e:
            raise ValueError(f"Error while building layers: {e}")

    def call(self, inputs, training=None):
        """Forward pass for the model."""
        x = inputs
        for layer in self.model_layers:
            x = layer(x)
        return x

    # TODO: serve solo per evitare il crasch al print prima della build
    def __repr__(self):
        try:
            return super().__repr__()
        except Exception:
            return f"<CustomModel name={self.custom_name} id={self.id}>"

    @staticmethod
    def convert_db_response(response, _dbm: DBManager):
        id = response[0]
        custom_name = response[2]
        tulp = _dbm.get_values("model_layer_relation", "id_layer, layer_index", "id_model", id)
        data_sorted = sorted(tulp, key=lambda tup: tup[1])
        sorted_layers_idx = [tup[0] for tup in data_sorted]
        list_of_layers = _dbm.retrieve_list_of_records("id", Layers.table_name, sorted_layers_idx)
        layers_objs: [Layers] = []
        for lay in list_of_layers:
            layers_objs.append(Layers.convert_db_response(lay))

        input_layers = [layer.layer["params"]["input_shape"][0] for layer in layers_objs if layer.type == "input"]

        model = CustomDQNModel(layers_objs, input_layers[0], custom_name, False, id)

        return model

    def set_up_layers(self, layers):
        """Ensure layers have DB IDs; push them if needed."""
        for idx, l in enumerate(layers):
            if isinstance(l.id, str) and self.push:
                l.push_on_db()
                l = Layers.convert_db_response(dbm.retrive_last('layers', '*'))
                layers[idx] = l
            self.layers_id.append(l.id)

    def to_tuple(self):
        """Serialize the model for DB insertion."""
        model_json = self.to_json()
        name = self.custom_name or "UnnamedModel"
        return (model_json, name, self.note)

    def push_on_db(self, notes='No Notes'):
        """Insert model and layer relationships into the DB."""
        try:
            self.note = notes
            super().push_on_db()
            self.id = dbm.retrive_last(self.table_name, 'id')[0]
            rel_data = [(self.id, lid, i) for i, lid in enumerate(self.layers_id)]
            dbm.push(rel_data, self.DB_RELATION_SCHEMA, self.DB_RELATION_INSERT_QUERY)
        except Exception as e:
            print(f"Error while saving model: {e}")

    @staticmethod
    def deserialize_from_json(json_str):
        """Deserialize a model from a JSON string."""
        config = json.loads(json_str)
        name = config.pop('name', None)
        model = tf.keras.models.model_from_json(json.dumps(config))
        model.name = name
        return model

    def save_model(self, path, save_format='h5'):
        """Save the model to file."""
        self.save(path, save_format=save_format)

    @staticmethod
    def load_model(path):
        """Load a model from file."""
        return tf.keras.models.load_model(path)

    def extract_standard_keras_model(self, shape):
        """Build a standard Keras Model object from internal layers."""
        try:
            x = k.Input(shape=shape.shape)
            for layer in self.model_layers:
                x = layer(x)
            return k.Model(inputs=x._keras_history[0], outputs=x)
        except Exception as e:
            print(f"Error generating standard Keras model: {e}")
            return None


