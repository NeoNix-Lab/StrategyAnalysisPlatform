
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from src.database.connection import Base
import src.database.models # Ensure models are registered
from src.api.main import app
from src.database.connection import get_db

# Setup in-memory DB for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}, 
    poolclass=StaticPool
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def client():
    # Create tables
    Base.metadata.create_all(bind=engine)
    with TestClient(app) as c:
        yield c
    # Drop tables
    Base.metadata.drop_all(bind=engine)

def test_ml_studio_crud_flow(client):
    """
    Test the full lifecycle of creating ML configurations and a session.
    """
    # 1. Create Reward Function
    rf_payload = {
        "name": "Test Reward",
        "description": "Simple test reward",
        "code": "def calculate_reward(env, action): env.last_reward = 1.0"
    }
    res_rf = client.post("/api/ml/studio/functions", json=rf_payload)
    assert res_rf.status_code == 200
    rf_id = res_rf.json()["function_id"]

    # 2. Create Model Architecture
    model_payload = {
        "name": "Test Model",
        "description": "Simple Dense",
        "layers_json": [{"type": "Dense", "units": 10}]
    }
    res_model = client.post("/api/ml/studio/models", json=model_payload)
    assert res_model.status_code == 200
    model_id = res_model.json()["model_id"]

    # 3. Create Training Process
    process_payload = {
        "name": "Test Process",
        "epochs": 5
    }
    res_proc = client.post("/api/ml/studio/processes", json=process_payload)
    assert res_proc.status_code == 200
    proc_id = res_proc.json()["process_id"]

    # 4. Create Session
    session_payload = {
        "name": "Test Session",
        "function_id": rf_id,
        "model_id": model_id,
        "process_id": proc_id
    }
    res_sess = client.post("/api/ml/studio/sessions", json=session_payload)
    assert res_sess.status_code == 200
    session_id = res_sess.json()["session_id"]
    
    # 5. List Sessions and Verify
    res_list = client.get(f"/api/ml/studio/sessions/{session_id}")
    assert res_list.status_code == 200
    data = res_list.json()
    assert data["name"] == "Test Session"
    assert data["function"]["id"] == rf_id

def test_iteration_lifecycle(client):
    # Setup prerequisite data (assuming previous test didn't persist if module scope used incorrectly, 
    # but with sqlite memory per module, we might need to recreate or rely on shared state. 
    # Better to recreate for isolation or use bigger fixture.)
    # For simplicity, we assume isolation or recreate minimal deps.
    
    # Need a dataset first (mocking one via direct DB insertion or API if exists)
    # Let's try to create a dataset via API (if we have one).
    # Assuming /api/datasets exists from previous work
    
    # Create Dummy Run & Dataset if needed, or just insert into DB directly for speed
    # But let's use the API flow
    
    # 1. Create Dataset
    ds_payload = {
        "name": "Test DS",
        "sources": [{"run_id": "dummy"}],
        "feature_config": ["close"]
    }
    # Note: This might fail if "dummy" run doesn't exist and API validates it. 
    # If API doesn't validate strictly, it passes.
    # If it validates, we must insert a run.
   
    # Let's interact with DB directly for setup to avoid robust massive setup
    with TestingSessionLocal() as db:
        from src.database.models import Dataset, MlTrainingSession, MlRewardFunction, MlModelArchitecture, MlTrainingProcess
        import uuid
        
        # Dataset
        ds = Dataset(dataset_id=str(uuid.uuid4()), name="Test DS", sources_json=[], feature_config_json=[])
        db.add(ds)
        
        # Session Dependencies
        rf = MlRewardFunction(function_id=str(uuid.uuid4()), name="RF", code="pass")
        model = MlModelArchitecture(model_id=str(uuid.uuid4()), name="Model", layers_json=[])
        proc = MlTrainingProcess(process_id=str(uuid.uuid4()), name="Proc")
        db.add(rf); db.add(model); db.add(proc)
        
        # Session
        sess = MlTrainingSession(session_id=str(uuid.uuid4()), name="Sess", function_id=rf.function_id, model_id=model.model_id, process_id=proc.process_id)
        db.add(sess)
        
        db.commit()
        
        ds_id = ds.dataset_id
        sess_id = sess.session_id

    # 2. Create Iteration
    iter_payload = {
        "session_id": sess_id,
        "dataset_id": ds_id,
        "name": "Test Iteration"
    }
    res_iter = client.post("/api/ml/studio/iterations", json=iter_payload)
    assert res_iter.status_code == 200
    iter_id = res_iter.json()["iteration_id"]
    
    # 3. Trigger Run
    res_run = client.get(f"/api/ml/studio/iterations/{iter_id}/run")
    assert res_run.status_code == 200
    assert res_run.json()["status"] == "QUEUED"
    
    # 4. Stop Run
    res_stop = client.post(f"/api/ml/studio/iterations/{iter_id}/stop")
    assert res_stop.status_code == 200
    assert res_stop.json()["status"] == "CANCELLING"
