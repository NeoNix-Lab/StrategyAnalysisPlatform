from ..service import db_manager as dbm
from .base_models import BaseModelsClass as BMC


class Iterazione(BMC):
    """
    Rappresenta un'iterazione di un processo di machine learning,
    collegando risultati di training, test e work a specifici set di dati.
    """

    DB_SCHEMA = '''
        CREATE TABLE IF NOT EXISTS iterazioni (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            dati_id INTEGER,
            training_id INTEGER,
            train_result REAL,
            test_result REAL,
            work_result REAL,
            log_path TEXT,
            FOREIGN KEY(dati_id) REFERENCES dati(id),
            FOREIGN KEY(training_id) REFERENCES training(id)
        );
    '''

    INSERT_QUERY = '''
        INSERT INTO iterazioni 
        (name, dati_id, training_id, train_result, test_result, work_result, log_path)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    '''

    table_name = "iterazioni"

    fields = [
        "name", "dati_id", "training_id",
        "train_result", "test_result", "work_result", "log_path"
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @staticmethod
    def update_result(iteration_id: int, update_dict: dict):
        """
        Aggiorna i risultati di un'iterazione esistente nel DB.

        Args:
            iteration_id (int): ID dell'iterazione da aggiornare.
            update_dict (dict): Dizionario dei campi da aggiornare.
        """
        dbm.new_update_record('iterazioni', update_dict, {'id': iteration_id})
