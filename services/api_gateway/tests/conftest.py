import pytest
import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

# Add project root to path to ensure imports work
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# Add src directory so the "api" package can be imported directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from quant_shared.models.models import Base

# Force in-memory DB for tests to avoid locking real DB
os.environ["TRADING_DB_PATH"] = ":memory:"

# Try to import app. If fails, client tests will fail but unit tests will pass.
try:
    from api.main import app
except ImportError:
    app = None

from sqlalchemy.pool import StaticPool

@pytest.fixture(scope="session")
def test_engine():
    # Use in-memory SQLite for speed and isolation
    # StaticPool is required to share the same in-memory DB across connections
    engine = create_engine(
        'sqlite:///:memory:', 
        connect_args={"check_same_thread": False},
        poolclass=StaticPool
    )
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
def client(test_engine):
    if app:
        from quant_shared.models.connection import get_db
        
        def override_get_db():
            # Bind the session to the connection
            TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
            session = TestingSessionLocal()
            try:
                yield session
            finally:
                session.close()

        app.dependency_overrides[get_db] = override_get_db
        with TestClient(app) as c:
            yield c
        app.dependency_overrides = {}
    else:
        yield None
