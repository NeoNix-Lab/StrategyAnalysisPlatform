import sqlite3
import pytest
from training_node.rl_rnn_core.models.reward_function import RewardFunction
from training_node.rl_rnn_core.models.dati import Dati
from training_node.rl_rnn_core.models.model_static import CustomDQNModel, Layers
from training_node.rl_rnn_core.models.iteration import Iterazione
from training_node.rl_rnn_core.models.process import Process
from training_node.rl_rnn_core.models.training_model import Training_Model
from training_node.rl_rnn_core.service.db_manager import DBManager as dbm
from tensorflow.keras import Model as KModel


# CustomDQNModel, Training_Model,
MODELS = [Dati, Iterazione,  Process, Layers,  RewardFunction]
_dbm = dbm()

def test_retrive_and_build():
    for model in MODELS:
        tulp = _dbm.retrieve_last(model.table_name, "id")
        obj = model.convert_db_response(tulp)
        assert isinstance(obj, model)
        if model == CustomDQNModel:
            modello_cutom : CustomDQNModel= obj
            assert isinstance(CustomDQNModel.deserialize_from_json(modello_cutom.model_layers), KModel)