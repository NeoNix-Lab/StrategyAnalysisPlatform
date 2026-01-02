from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

# Per ora usiamo SQLite locale
# Default resolution logic:
# 1. Environment variable
# 2. Search for existing DB in parent directories (to find project root from services)
# 3. Fallback to local new file
DB_PATH = os.getenv("TRADING_DB_PATH")

if not DB_PATH:
    # Smart fallback: search for existing DB
    potential_paths = [
        "trading_data.db",                # Current dir
        "../../trading_data.db",          # 2 levels up (from services/xyz)
        "../../../trading_data.db"        # 3 levels up
    ]
    for p in potential_paths:
        if os.path.exists(os.path.abspath(p)):
            DB_PATH = os.path.abspath(p)
            print(f"🔄 Database found at: {DB_PATH}")
            break

if not DB_PATH:
    DB_PATH = "trading_data.db" # Default fallback

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
