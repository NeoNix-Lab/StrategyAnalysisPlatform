from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

from sqlalchemy.pool import StaticPool

# Default to local SQLite, but allow override via env var (e.g. for tests)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///trading_data.db")

from sqlalchemy import event

# For in-memory SQLite, we must use StaticPool to share the same database across connections
engine_args = {"echo": False, "connect_args": {"check_same_thread": False, "timeout": 10}}
if DATABASE_URL == "sqlite:///:memory:":
    engine_args["poolclass"] = StaticPool

engine = create_engine(DATABASE_URL, **engine_args)

# Enable Write-Ahead Logging (WAL) for better concurrency
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL") # Optional: trade some safety for speed
    cursor.close()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Crea le tabelle nel database se non esistono."""
    # Crea solo le tabelle mancanti, senza cancellare i dati esistenti
    Base.metadata.create_all(bind=engine)
    print(f"Database inizializzato su {DATABASE_URL}")
    print(f"Tabelle conosciute: {list(Base.metadata.tables.keys())}")

def get_db():
    """Dependency per ottenere una sessione DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
