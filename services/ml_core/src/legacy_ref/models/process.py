from enum import Enum
from ..service import db_manager as dbm
from .base_models import BaseModelsClass as BCM

class process_type(Enum):
    """
    Enumeration for process execution types.
    """
    BATCH = 'batch'
    SERIE = 'serie'
    STEP = 'step'

class ProcessOptimizer(Enum):
    """
    Enumeration of supported optimizers.
    """
    ADAM = 'Adam'
    SGD = 'SGD'
    RMSPROP = 'RMSprop'
    ADAGRAD = 'Adagrad'
    ADADELTA = 'Adadelta'
    NADAM = 'Nadam'
    FTRL = 'Ftrl'
    ADAMAX = 'Adamax'

class ProcessLossFunction(Enum):
    """
    Enumeration of supported loss functions.
    """
    MEAN_SQUARED_ERROR = 'mean_squared_error'
    BINARY_CROSSENTROPY = 'binary_crossentropy'
    CATEGORICAL_CROSSENTROPY = 'categorical_crossentropy'
    SPARSE_CATEGORICAL_CROSSENTROPY = 'sparse_categorical_crossentropy'
    MEAN_ABSOLUTE_ERROR = 'mean_absolute_error'
    HINGE = 'hinge'
    HUBER = 'huber'
    LOGCOSH = 'logcosh'
    KULLBACK_LEIBLER_DIVERGENCE = 'kullback_leibler_divergence'

class Process(BCM):
    """
    Represents a process configuration for reinforcement learning or machine learning.
    Inherits from BaseModelsClass to enable database integration and common behavior.
    """

    table_name = "processes"

    fields = [
        "name", "description", "epsilon_start", "epsilon_end", "epsilon_reduce",
        "gamma", "tau", "learning_rate", "optimizer", "loss", "n_episode",
        "epochs", "type", "window_size", "fees", "initial_balance", "batch_size"
    ]

    DB_SCHEMA = '''CREATE TABLE IF NOT EXISTS processes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        description TEXT,
        epsilon_start REAL,
        epsilon_end REAL,
        epsilon_reduce REAL,
        gamma REAL,
        tau REAL,
        learning_rate REAL,
        optimizer TEXT,
        loss TEXT,
        n_episode INTEGER,
        epochs INTEGER,
        type TEXT,
        windows_size REAL,
        fees REAL,
        initialBalance REAL,
        batch_size REAL
    );'''

    INSERT_QUERY = '''INSERT INTO processes (
        name, description, epsilon_start, epsilon_end, epsilon_reduce, gamma, tau,
        learning_rate, optimizer, loss, n_episode, epochs, type, windows_size,
        fees, initialBalance, batch_size
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);'''

    def __init__(self, **kwargs):
        # Convert enums to values if passed as enum instances
        if isinstance(kwargs.get("optimizer"), ProcessOptimizer):
            kwargs["optimizer"] = kwargs["optimizer"].value
        if isinstance(kwargs.get("loss"), ProcessLossFunction):
            kwargs["loss"] = kwargs["loss"].value
        if isinstance(kwargs.get("type"), process_type):
            kwargs["type"] = kwargs["type"].value

        super().__init__(**kwargs)

    @classmethod
    def convert_db_response(cls, row):
        """
        Converts a database row to a Process instance.

        Parameters:
        - row (tuple): A tuple of values corresponding to the database row.

        Returns:
        - Process: An instance of the Process class populated with the row data.
        """
        data = dict(zip(("id", *cls.fields), row))
        # Re-convert fields that are Enums
        data["optimizer"] = ProcessOptimizer(data["optimizer"])
        data["loss"] = ProcessLossFunction(data["loss"])
        data["type"] = process_type(data["type"])
        return cls(**data)

    @staticmethod
    def retrive_list_records_by_name(names: list[str]):
        """
        Retrieve all Process records with a given list of names.

        Parameters:
        - names (list[str]): List of process names.

        Returns:
        - list: List of DB rows matching the given names.
        """
        return dbm.retive_a_list_of_recordos('name', 'processes', names)

    def print_attributo(self, nome_attributo):
        """
        Print the value and type of an attribute by name.

        Parameters:
        - nome_attributo (str): The attribute name.
        """
        if hasattr(self, nome_attributo):
            valore = getattr(self, nome_attributo)
            tipo = type(valore).__name__
            print(f'Attribute: {nome_attributo} | Value: {valore} | Type: {tipo}')
        else:
            print(f"The attribute '{nome_attributo}' does not exist.")
