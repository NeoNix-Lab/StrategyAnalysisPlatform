import pandas as pd
import json
from ..service import db_manager as dbm
from ..service.data_retriver import DataRetriever
from .base_models import BaseModelsClass


class Dati(BaseModelsClass):
    """
    Represents the data used in machine learning processes.

    Handles DB schema, insertion, and preprocessing of train/work/test splits.

    Attributes:
    -----------
    DB_SCHEMA : str
    insert_query : str
    fields : list
    table_name : str
    """

    DB_SCHEMA = '''CREATE TABLE IF NOT EXISTS dati (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        train_data REAL,
        work_data REAL,
        test_data REAL,
        decrease_data REAL,
        db_references TEXT,
        colonne TEXT
    );'''

    insert_query = '''INSERT INTO dati 
        (name, train_data, work_data, test_data, decrease_data, db_references, colonne)
        VALUES (?, ?, ?, ?, ?, ?, ?);'''

    fields = ["name", "train_data", "work_data", "test_data", "decrease_data", "db_references", "colonne"]
    table_name = "dati"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.df_or_colonne = self.serializza_colonne(kwargs.get("colonne"))
        self._setup_data()

    #@classmethod
    #def convert_db_response(cls, row):
    #    print("DEBUG row:", row, type(row))
    #    keys = ("id", *cls.fields)
    #    data = dict(zip(keys, row))
    #    return cls(**data)


    def _setup_data(self):
        if not hasattr(self, 'name') or not self.name:
            raise ValueError("Missing 'name' attribute required for data fetching.")

        try:
            retriver = DataRetriever(self.db_references)
            df = retriver.fetch_data(self.name)
            self.data = self.riduci_df_alle_colonne(df)
        except Exception as e:
            raise ValueError(f'Error retrieving data: {e}')

        self.train_data_ = self.data[: int(len(self.data) * self.train_data)]

        if self.work_data > 0:
            start = int(len(self.data) * self.train_data)
            end = start + int(len(self.data) * self.work_data)
            self.work_data_ = self.data[start:end]
        else:
            self.work_data_ = None

        if self.test_data > 0:
            start = len(self.data) - int(len(self.data) * self.test_data)
            self.test_data_ = self.data[start:]
        else:
            self.test_data_ = None

    def serializza_colonne(self, df_or_colonne):
        """
        Serializes a list of columns from a pandas DataFrame or list to JSON.

        Returns:
        --------
        - str: JSON string of column names.
        """
        if isinstance(df_or_colonne, pd.DataFrame):
            colonne = df_or_colonne.columns.tolist()
        elif isinstance(df_or_colonne, list) and all(isinstance(c, str) for c in df_or_colonne):
            colonne = df_or_colonne
        else:
            try:
                colonne = json.loads(df_or_colonne)
            except Exception as e:
                raise ValueError(f"Invalid column format: {e}")

        return json.dumps(colonne)

    def riduci_df_alle_colonne(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Reduces the DataFrame to only the specified columns.

        Returns:
        --------
        - pd.DataFrame: reduced DataFrame
        """
        colonne = json.loads(self.df_or_colonne)
        return df[colonne]
