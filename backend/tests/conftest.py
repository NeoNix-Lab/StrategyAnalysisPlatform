import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add project root to path to ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Force a temporary file database for all tests 
# This is more robust than :memory: when multiple connections/threads are involved
import tempfile
_db_fd, _db_path = tempfile.mkstemp(suffix=".db")
os.environ["DATABASE_URL"] = f"sqlite:///{_db_path}"
# Close the fd but keep the path
os.close(_db_fd)

from src.database.models import Base, Strategy, StrategyInstance
# Try to import app. If fails, client tests will fail but unit tests will pass.
try:
    from src.api.main import app
except ImportError:
    app = None

@pytest.fixture(scope="session")
def test_engine():
    # Force in_memory for all tests
    from src.database.connection import engine
    from src.database.models import Base
    Base.metadata.create_all(bind=engine)
    return engine

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Creates a new database session for a test."""
    from src.database.connection import SessionLocal
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@pytest.fixture(scope="module")
def client():
    if app:
        # The app already uses the global engine from src.database.connection
        # which we forced to :memory: in the module-level code above.
        # We just need to ensure init_db is called.
        from src.database.connection import init_db
        init_db()
        with TestClient(app) as c:
            yield c
    else:
        yield None
