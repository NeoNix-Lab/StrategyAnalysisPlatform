import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add project root to path to ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from quant_shared.models.models import Base
# Try to import app. If fails, client tests will fail but unit tests will pass.
try:
    from api.main import app
except ImportError:
    app = None

@pytest.fixture(scope="session")
def test_engine():
    # Use in-memory SQLite for speed and isolation
    engine = create_engine('sqlite:///:memory:', connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Creates a new database session for a test."""
    connection = test_engine.connect()
    transaction = connection.begin()
    
    # Bind the session to the connection
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()

    yield session

    # Rollback the transaction after the test
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="module")
def client():
    if app:
        with TestClient(app) as c:
            yield c
    else:
        yield None
