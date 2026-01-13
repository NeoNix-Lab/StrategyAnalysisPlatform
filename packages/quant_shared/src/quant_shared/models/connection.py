from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

from pathlib import Path

# Per ora usiamo SQLite locale
# Logic: Always prefer the project root 'trading_data.db'
# We dertermine project root relative to this file's location in packages/quant_shared
# This file is in: .../Main/packages/quant_shared/src/quant_shared/models/connection.py

DB_PATH = os.getenv("TRADING_DB_PATH")

if not DB_PATH:
    # Anchor to this file
    current_file = Path(__file__).resolve()
    # Go up 5 levels to reach 'Main' from 'packages/quant_shared/src/quant_shared/models'
    # levels: models -> quant_shared -> src -> quant_shared -> packages -> Main
    project_root = current_file.parents[5]
    
    expected_db = project_root / "trading_data.db"
    
    if expected_db.exists():
        DB_PATH = str(expected_db)
        print(f"Database found at Project Root: {DB_PATH}")
    else:
        # Fallback only if root DB not found (rare, or first init)
        # Try to find it in CWD or parents as before, just in case structure differs
        potential_paths = [
            "trading_data.db", 
            "../../trading_data.db",
            "../../../trading_data.db"
        ]
        found = False
        for p in potential_paths:
            if os.path.exists(os.path.abspath(p)):
                DB_PATH = os.path.abspath(p)
                print(f"Database found at: {DB_PATH}")
                found = True
                break
        
        if not found:
             # Default to creating it in Root if possible, otherwise CWD
             DB_PATH = str(expected_db)
             print(f"Database target set to Project Root (New): {DB_PATH}")

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
