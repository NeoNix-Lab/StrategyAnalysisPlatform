import logging
from fastapi.testclient import TestClient
import sys
import os
import json

# Adjust path to include the service src directory
sys.path.append(os.path.join(os.path.dirname(__file__), "../src"))

from main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_training_flow():
    # 1. Create dummy data
    data = []
    for i in range(100):
        data.append({
            "close": i * 1.0,
            "volume": 100 + i,
            # We need enough columns to match a hypothetical window? 
            # Actually EnvFlex uses all columns.
        })

    # 2. Define Model Architecture
    layers = [
        {
            "type": "input",
            "layer": {
                "type": "Dense",
                "params": {"input_shape": [10, 2]} # 2 features: close, volume
            }
        },
        {
            "type": "hidden", # Meta type
            "layer": {
                "type": "LSTM",
                "params": {"units": 10, "return_sequences": False}
            }
        },
        {
            "type": "output",
            "layer": {
                "type": "Dense",
                "params": {"units": 3, "activation": "linear"} # 3 actions
            }
        }
    ]

    # 3. Request Payload
    payload = {
        "run_id": "test_run_001",
        "config": {
            "model_architecture": layers,
            "training_params": {
                "batch_size": 4, # Small batch for test
                "epochs": 1,     # 1 epoch
                "window_size": 10
            },
            "data": data
        }
    }

    # 4. Send Request
    response = client.post("/train", json=payload)
    assert response.status_code == 200
    resp_json = response.json()
    assert "job_id" in resp_json
    assert resp_json["status"] == "PENDING"
    
    job_id = resp_json["job_id"]
    print(f"Job ID: {job_id}")

    # 5. Poll Status (optional, manual check logic in unit test usually mocks background tasks, 
    # but TestClient runs them synchronously if using recent Starlette/FastAPI versions?
    # Actually BackgroundTasks in TestClient run *after* response is sent. 
    # So we can check status immediately after?)
    
    # Wait/Poll
    # with TestClient, background tasks are executed.
    
    # Let's check status again
    response = client.get(f"/status/{job_id}")
    status = response.json()["status"]
    print(f"Job Status: {status}")
    
    # It might still be running or completed. 
    # Since we are not mocking the Trainer, this will actually run TensorFlow traning!
    # It might be slow.
