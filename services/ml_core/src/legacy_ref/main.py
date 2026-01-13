from .models.reward_function import RewardFunction
from .models.dati import Dati
from .models.model_static import CustomDQNModel, Layers
from .models.iteration import Iterazione
from .models.process import Process
from .models.training_model import Training_Model
from .service.db_manager import DBManager as dbm
from .service.data_retriver import DataRetriever
from typing import  Literal
import pandas as pd
from .core.flex_env_refactored import EnvFlex

MODELS = {cls.__name__: None for cls in [
    RewardFunction, Dati, Iterazione, CustomDQNModel, Process, Layers, Training_Model
]}

# TODO missing type for resoult path

DBM = None
DTR = None
LOGS = None


def init_services(db_path, dati_path, result_path="C:\\Users\\user\\OneDrive\\Desktop\\DB_Models_Logs"):
    global DBM, DTR, LOGS

    if db_path is not None:
        DBM = dbm(db_path)
    else:
        DBM = dbm()

    LOGS = result_path


    if dati_path is not None:
        DTR = DataRetriever(dati_path)
    else:
        DTR = DataRetriever()

def _build_static_model_from_id(id:int, input_shape:int):
    try:
        model_ = DBM.retrieve_item(CustomDQNModel.table_name, 'id', id)

        list_layers = DBM.get_values("model_layer_relation", "id_layer, layer_index", "id_model", 2)
        layers_sorted = sorted(list_layers, key=lambda tup: tup[1])
        layers_tulpe = DBM.retrieve_list_of_records("id", Layers.table_name, [x[0] for x in layers_sorted])
        layers_obj = [Layers.convert_db_response(layer) for layer in layers_tulpe]
        MODELS["Layers"] = layers_obj

        MODELS["CustomDQNModel"] = CustomDQNModel(layers_obj, input_shape, model_[2], False)

    except ValueError as e:
        raise(f'errore nella costruzione del modello statico dal id : ################################{e}')

def _ensure_initialized():
    if DBM is None or DTR is None:
        raise RuntimeError("init_services() First")


def get_model(name: str):
    model = MODELS.get(name)
    if model is None:
        raise RuntimeError(f"Model {name} non inizializzato.")
    return model


def set_instance(name: str, instance):
    """
    Assegna direttamente un’istanza di modello esistente al dizionario.
    """
    if name not in MODELS:
        raise KeyError(f"Modello '{name}' non riconosciuto.")
    MODELS[name] = instance
    return instance

def build_iteration_from_it_id(id):
    """
    Costruisce e ritorna gli oggetti Function, Process e Model da un record di training.

    Args:
        record (tuple): Un record del database rappresentante un training.

    Returns:
        tuple: Una tupla contenente tre oggetti in questo ordine specifico:
            - Rewar_Function: Loggetto Function costruito dal record del database.
            - Process: Loggetto Process costruito dal record del database.
            - Model: Loggetto Model costruito utilizzando l ID modello dal record del training e la dimensione della finestra dal Process.

    Raises:
        Exception: Solleva un eccezione se c e un errore nella costruzione degli oggetti dal record del training.
    """
    _ensure_initialized()
    try:
        record = DBM.retrieve_item(Iterazione.table_name, "id", id)
        MODELS["Iterazione"] = Iterazione.convert_db_response(record)

        dati = DBM.retrieve_item(Dati.table_name, "id", MODELS["Iterazione"].dati_id)
        MODELS["Dati"] = Dati.convert_db_response(dati)

        build_training_from_tr_id(MODELS["Iterazione"].training_id)

    except Exception as e:
        raise(e)



def build_training_from_tr_id(id):
    """
    Costruisce e ritorna gli oggetti Function, Process e Model da un record di training.

    Args:
        record (tuple): Un record del database rappresentante un training.

    Returns:
        tuple: Una tupla contenente tre oggetti in questo ordine specifico:
            - Rewar_Function: Loggetto Function costruito dal record del database.
            - Process: Loggetto Process costruito dal record del database.
            - Model: Loggetto Model costruito utilizzando l ID modello dal record del training e la dimensione della finestra dal Process.

    Raises:
        Exception: Solleva un eccezione se c e un errore nella costruzione degli oggetti dal record del training.
    """
    _ensure_initialized()
    try:
        record = DBM.retrieve_item(Training_Model.table_name, "id", id)
        MODELS["Training_Model"] = Training_Model.convert_db_response(record)

        _process = DBM.retrieve_item(Process.table_name, 'id', MODELS["Training_Model"].process_id)
        MODELS["Process"] = Process.convert_db_response(_process)

        _function = DBM.retrieve_item(RewardFunction.table_name, 'id', MODELS["Training_Model"].function_id)
        MODELS["RewardFunction"] = RewardFunction.convert_db_response(_function)
        _model = _build_static_model_from_id(MODELS["Training_Model"].model_id, MODELS["Process"].window_size)


    except Exception as e:
        raise(e)

DataSet = Literal["train_data_", "work_data_", "test_data_"]
def build_and_test_envoirment(data: DataSet, test_action:int=1):
    exec(MODELS["RewardFunction"].function)


    globals()["flex_buy_andSell"] = locals()['flex_buy_andSell']
    globals()["fillTab"] = locals()['fillTab']
    globals()['premia'] = locals()['premia']
    dataset = MODELS["Dati"].data

    data_set: pd.DataFrame = pd.DataFrame(dataset)

    action_space = pd.DataFrame([MODELS["RewardFunction"].action_schema]).columns
    position_space = pd.DataFrame([MODELS["RewardFunction"].status_schema]).columns

    #env = EnvFlex(data_set, globals()['premia'], [], action_space, position_space, int(MODELS["Process"].window_size), MODELS["Process"].fees, MODELS["Process"].initial_balance, use_additional_reward_colum=False)
    env = EnvFlex(data_set, int(MODELS["Process"].window_size), globals()['flex_buy_andSell'], action_space)

    test_step = env.step(test_action)

    return test_step
