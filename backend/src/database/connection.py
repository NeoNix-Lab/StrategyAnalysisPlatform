from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base
import os

# Per ora usiamo SQLite locale
DB_PATH = "trading_data.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
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
