# base_models_class.py

from abc import ABC, abstractmethod
from typing import ClassVar, Sequence, Any, Tuple, Type, TypeVar
from ..service import db_manager as dbm
# TODO centralizzare la gestione del db
from auth_db_neonix.services.sqlite_service import SQLiteManager

T = TypeVar("T", bound="BaseModelsClass")

class BaseModelsClass(ABC):
    """
    Classe base per tutti i model che mappano una riga di DB.
    Le sottoclassi devono dichiarare:
      - table_name: nome della tabella
      - fields: elenco ordinato dei nomi degli attributi (sans 'id')
      - DB_SCHEMA e INSERT_QUERY (come stringhe)
    """

    # metadati da definire in ogni sottoclasse
    table_name: ClassVar[str]
    fields:    ClassVar[Sequence[str]]  # es. ["name","dati_id",…]
    DB_SCHEMA: ClassVar[str]
    INSERT_QUERY: ClassVar[str]

    def __init__(self, **kwargs):
        # popola self.<field> e self.id
        for f in ("id", *self.fields):
            setattr(self, f, kwargs.get(f))

    def to_tuple(self) -> Tuple[Any, ...]:
        """Costruisce la tupla di valori da inserire (in ordine fields)."""
        return tuple(getattr(self, f) for f in self.fields)

    def push_on_db(self, notes: str = "") -> None:
        """Crea la tabella (se non esiste) e inserisce il record."""
        # 1) crea la tabella
        dbm.push((), self.DB_SCHEMA, self.DB_SCHEMA)  # qui potresti avere un metodo dedicato create_table
        # 2) inserisci i dati
        dbm.push([self.to_tuple()],        # lista di tuple
                 self.table_name,          # usato solo per segnalazioni
                 self.INSERT_QUERY)


    @classmethod
    def convert_db_response(cls: Type[T], row: Tuple[Any, ...]) -> T:
        """Dà in pasto al costruttore id + campi, restituendo l’istanza."""
        # assumiamo che row = (id, *values_in_fields_order)
        data = dict(zip(("id", *cls.fields), row))
        return cls(**data)
