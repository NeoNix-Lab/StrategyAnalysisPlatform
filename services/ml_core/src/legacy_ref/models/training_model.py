from enum import Enum
from ..service import db_manager as dbm
from datetime import datetime as dt
from .base_models import BaseModelsClass as BCM

#TODO: manca la documentazione

class Training_statu(Enum):
    PLANNED = 'planned'
    TESTED = 'tested'
    TRAINED = 'trained'

class Training_Model(BCM):
    table_name = 'training'
    # TODO: aggiungere i trading data as dictionary fees, initial_balance
    DB_SCHEMA = '''CREATE TABLE IF NOT EXISTS training (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               status TEXT,
               creation_date TEXT,
               function_id INTEGER,
               process_id INTEGER,
               model_id INTEGER,
               log_path TEXT,
               best_result REAL,
               notes TEXT,
               name TEXT,
               FOREIGN KEY (function_id) REFERENCES functions(id),
               FOREIGN KEY (model_id) REFERENCES models(id),
               FOREIGN KEY (process_id) REFERENCES processes(id) 
           );
           '''

    INSERT_QUERY = '''INSERT INTO training (status, creation_date, function_id, process_id, model_id, log_path, best_result, notes, name)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);'''

    def __init__(self, name, status:Training_statu, function_id, process_id, model_id, log_path, id='not_posted_yet',
                 creation_data=dt.now().strftime('%Y-%m-%d %H:%M:%S'), best_resoult=0):
        self.id = id
        self.status = status
        self.function_id = function_id
        self.process_id = process_id
        self.model_id = model_id
        self.creation_date = creation_data
        self.log_path = log_path
        self.best_resoult = best_resoult
        self.name = name
        self.attributi = self.__dict__.copy()

    def push_on_db(self, notes='No Notes'):
        data_tulpe = [(self.status.value, self.creation_date, self.function_id, self.process_id, self.model_id, self.log_path, self.best_resoult, notes, self.name)]
        obj = dbm.push(data_tulpe, self.DB_SCHEMA, self.INSERT_QUERY, 'name', 8, 'training')
        #TODO:sto ritornando in modo un po confuso una db response
        if obj != []:
            return Training_Model.convert_db_response(obj[0])
        

    @staticmethod
    def convert_db_response(response):
         try:
             status = Training_statu(response[1])
             obj = Training_Model(response[9], status, response[3], response[4], model_id=response[5], id=response[0], creation_data=response[2],
                                  log_path=response[6], best_resoult=response[7])
             return obj
         except ValueError as e:
             raise(f"Errore durante la mappatura del record su Training_Model: {e}")
        

    # TODO: some implementation not implemented
    def update_status(self, status: Training_statu):
        stat = status.value
        update_dict = {'status': stat}
        requ_dict = {'id': self.id}
        dbm.new_update_record(self.DB_TAB_NAME, update_dict, requ_dict)

    def update_best_resoult(self, best_resoult):
        override = False
        try:
            if float(self.best_resoult) < best_resoult:
                override = True
        except:
            override = True

        if override == True:
            update_dict = {'best_result': best_resoult}
            requ_dict = {'id': self.id}
            dbm.new_update_record(self.DB_TAB_NAME, update_dict, requ_dict)

    def update_path(self, path):
        update_dict = {'log_path': path}
        requ_dict = {'id': self.id}
        dbm.new_update_record(self.DB_TAB_NAME, update_dict, requ_dict)

    def update_notes(self, notes):
        update_dict = {'notes': notes}
        requ_dict = {'id': self.id}
        dbm.new_update_record(self.DB_TAB_NAME, update_dict, requ_dict)

    @staticmethod
    def retrive_list_records_by_name(names: list[str]):
        return dbm.retive_a_list_of_recordos('name', 'processes', names)
