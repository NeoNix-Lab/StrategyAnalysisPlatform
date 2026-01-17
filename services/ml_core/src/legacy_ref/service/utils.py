from ..core.training_model import Training_Model as tr_mod
from ..service import db_manager as db
from ..core.process import Process
from ..core.reward_function import Rewar_Function as rw
from ..core.iteration import Iterazione
from ..core.model_static import CustomDQNModel as Models
from ..core.model_static import Layers as Layers
from ..core.dati import Dati
from .config import Config
from ..core.flex_envoirment import EnvFlex as flex
import pandas as pd
from typing import Callable

DEFOULT_CODE = '''
def flex_buy_andSell(env, price_column_name: str, action: str):
    price = env.Obseravtion_DataFrame[price_column_name][env.current_step]
    _, action_array, action_name, _ = env.Endcode(env.action_space_tab, action)
    _, status_array, statuscode, _ = env.Endcode(env.position_tab, env.last_position_status)
    _fees = env.calculatefees()

    if action_name == 'buy':
        if statuscode == 'flat' or statuscode == 0:
            env.last_qty_both = env.current_balance / price
            env.last_Reward = 0
            env.last_position_status = 'long'

        elif statuscode == 'short' or statuscode == 2:
            gain = (env.last_qty_both * price) - env.current_balance
            env.last_Reward = gain
            env.current_balance += gain
            env.last_position_status = 'flat'
            env.last_qty_both = 0

        elif statuscode == 'long' or statuscode == 1:
            env.last_Reward = 0

    elif action_name == 'sell':
        if statuscode == 'flat' or statuscode == 0:
            env.last_Reward = 0
            env.last_qty_both = env.current_balance / price
            env.last_position_status = 'short'

        elif statuscode == 'long' or statuscode == 1:
            gain = (env.last_qty_both * price) - env.current_balance
            env.last_Reward = gain
            env.current_balance += gain
            env.last_position_status = 'flat'
            env.last_qty_both = 0

        elif statuscode == 'short' or statuscode == 2:
            env.last_Reward = 0

    if env.current_balance <= 0:
        env.done = True

def fillTab(env):
    step = env.current_step
    env.Obseravtion_DataFrame.loc[step, 'position_status'] = env.last_position_status
    env.Obseravtion_DataFrame.loc[step, 'step'] = env.current_step
    env.Obseravtion_DataFrame.loc[step, 'action'] = env.last_action
    env.Obseravtion_DataFrame.loc[step, 'balance'] = env.current_balance
    env.Obseravtion_DataFrame.loc[step, 'reward'] = env.last_Reward

# Definisco la funzione di premio
def premia(env, action):
    flex_buy_andSell(env, 'Price', action)
    fillTab(env)

schema = {
 'Action_Schema': {'wait': None, 'buy': None, 'sell': None}, 
 'Status_Schema': {'flat': None, 'long': None, 'short': None}
}

'''

# HACK: migliore il suggerimento
CODE_HINT = """
f_Premia: racchiude funzioni di ricompensa e di aggiornamento 
schema: lista di dizionari
    0:data 
    1:action 
    2:status
"""

object_mapping = {
    'dati': Dati,
    'training': tr_mod,
    #'models': Models, ---- NON C e TODO
    'layers': Layers,
    'iterazioni': Iterazione,
    'functions': rw,
    'processes': Process
}

def retrive_generic_obj(obj_type:str, db_config:Config):
    lis = []
    lis_name = []
    ids = []
    records = None
    error = ''
    try:
        records = db.retrive_all(obj_type)

        obj_class = object_mapping.get(obj_type.lower())

        for obj in records:
            if obj_type == "training" or obj_type == "iterazioni":
                var = obj_class.convert_db_response(obj)
            else:
                var = obj_class.convert_db_response(obj,db_config)

            lis.append(var)
            lis_name.append(var.name)
            ids.append(var.id)
    except ValueError as e:
        error = e

    return lis, lis_name, ids, error


def compare_function_to_dati(function_obj:rw, dati_obj:Dati):
    chiavi = [i for i in function_obj.data_schema.keys()]
    columns = [i for i in dati_obj.data.columns]

    return chiavi == columns

def text_column_metrics(df, column):
    metrics = {}
    metrics['Total Entries'] = len(df[column])
    metrics['Unique Entries'] = df[column].nunique()
    metrics['Most Frequent Entry'] = df[column].mode().values[0]
    metrics['Average Length'] = df[column].astype(str).apply(len).mean()
    metrics['Max Length'] = df[column].astype(str).apply(len).max()
    metrics['Min Length'] = df[column].astype(str).apply(len).min()
    return metrics

def sort_list_of_layers_from_record(record):
    sorted_record = sorted(record, key=lambda x: x[2])
    sorted_indexes = [item[1] for item in sorted_record]
    return sorted_indexes

def build_static_model_from_id(id:[int], input_shape:int):
    try:
        model_ = db.retive_a_list_of_recordos('id', 'models', id)
        _model = model_[0]

        list_layers = db.retive_a_list_of_recordos('id_model', 'model_layer_relation', id)

        list_of_indexses = sort_list_of_layers_from_record(list_layers)

        layers_ = db.retive_a_list_of_recordos('id', 'layers', list_of_indexses)

        lay = []
        for i in layers_:
            obj = Layers.convert_db_response(i)
            lay.append(obj)

        if id == int(_model[0]):
            return Models(lay,input_shape,_model[2],id=id,push=False)
        else:
            raise ValueError('retrived wrong model from db')

    except ValueError as e:
        raise(f'errore nella costruzione del modello statico dal id : ################################{e}')

def build_and_test_envoirment(data:pd.DataFrame, function:rw, process:Process, test_action:int=1, test_function:Callable=None):
    action_space = list(pd.DataFrame([function.action_schema]).columns)
    position_space = list(pd.DataFrame([function.status_schema]).columns)

    exec(function.funaction)

    #HINT: per rendere accessibili a livello globale funzioni stringate e necessario recuperarle e reindirizzarle
    globals()["flex_buy_andSell"] = locals()['flex_buy_andSell']
    globals()["fillTab"] = locals()['fillTab']
    globals()['premia'] = locals()['premia']

    if test_function == None:
        env = flex(data,globals()['premia'],[],action_space,position_space,int(process.window_size),process.fees,process.initial_balance)
    else:
        env = flex(data,test_function,[],action_space,position_space,int(process.window_size),process.fees,process.initial_balance)

    s = env.step(test_action)
    print(f'[[[[[[[[[[[[[[[{s[0].head(30)}]]]]]]]]]]]]]]]')

    return env, env.Obseravtion_DataFrame
