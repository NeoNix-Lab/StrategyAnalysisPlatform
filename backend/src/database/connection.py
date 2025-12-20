from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

# Per ora usiamo SQLite locale
DB_PATH = "trading_data.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

from sqlalchemy import event

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False, "timeout": 10})

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

def get_db():
    """Dependency per ottenere una sessione DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
