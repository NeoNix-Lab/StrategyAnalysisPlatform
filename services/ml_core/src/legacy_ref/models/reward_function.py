import json
from typing import Optional
from .base_models import BaseModelsClass

class RewardFunction(BaseModelsClass):
    table_name: str = "functions"
    fields = ["name", "function", "data_schema", "action_schema", "status_schema", "notes"]

    DB_SCHEMA = """
    CREATE TABLE IF NOT EXISTS functions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        function TEXT,
        data_schema TEXT,
        action_schema TEXT,
        status_schema TEXT,
        notes TEXT
    );
    """

    INSERT_QUERY = """
    INSERT INTO functions (name, function, data_schema, action_schema, status_schema, notes)
    VALUES (?, ?, ?, ?, ?, ?);
    """

    def __init__(
            self,
            name: str,
            function: str,
            data_schema: dict,
            action_schema: dict,
            status_schema: dict,
            notes: str = "",
            id: Optional[int] = None
    ):
        # Serializza i dict in JSON-string per il DB
        super().__init__(
            id=id,
            name=name,
            function=function,
            data_schema=json.dumps(data_schema),
            action_schema=json.dumps(action_schema),
            status_schema=json.dumps(status_schema),
            notes=notes
        )
        # Mantieni i dict decodificati per l’uso in memoria
        self.data_schema = data_schema
        self.action_schema = action_schema
        self.status_schema = status_schema

    def push_on_db(self) -> None:
        super().push_on_db()  # crea tabella e inserisce

    @classmethod
    def convert_db_response(cls, row) -> "RewardFunction":
        # row = (id, name, function, data_schema_json,
        #        action_schema_json, status_schema_json, notes)
        id_, name, func_str, data_json, action_json, status_json, notes = row

        # JSON -> dict
        try:
            data_schema = json.loads(data_json)
        except ValueError:
            data_schema = {}
        try:
            action_schema = json.loads(action_json)
        except ValueError:
            action_schema = {}
        try:
            status_schema = json.loads(status_json)
        except ValueError:
            status_schema = {}

        # Costruisci l’istanza con i dict
        return cls(
            name=name,
            function=func_str,
            data_schema=data_schema,
            action_schema=action_schema,
            status_schema=status_schema,
            notes=notes,
            id=id_
        )

