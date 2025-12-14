import pytest
import time
import uuid
from datetime import datetime

# Tests depend on 'client' fixture from conftest.py
# If client is None (app import failed), rely on pytest.mark.skip or similar
# But here we just assume it works or fails with a clear error.

def test_flow(client):
    if client is None:
        pytest.skip("API Client not available (likely import error in conftest)")

    print("--- Starting Integration Flow Test (TestClient) ---")
    
    # 1. Start Run
    print("\n1. Starting Run...")
    start_payload = {
        "strategy_id": "TEST_STRAT_INTEGRATION",
        "parameters": {"param1": 10, "param2": "test"},
        "data_range": {"symbol": "EURUSD", "timeframe": "M1"}
    }
    
    resp = client.post("/runs/start", json=start_payload)
    if resp.status_code != 200:
        pytest.fail(f"FAILED to start run: {resp.text}")
    
    run_data = resp.json()
    run_id = run_data['run_id']
    print(f"SUCCESS: Run started with ID: {run_id}")
    
    # 2. Ingest Data (Orders & Executions)
    print("\n2. Ingesting Stream Data...")
    
    order_id = str(uuid.uuid4())
    exec_id = str(uuid.uuid4())
    
    stream_payload = {
        "orders": [
            {
                "order_id": order_id,
                "run_id": run_id,
                "strategy_id": "TEST_STRAT_INTEGRATION",
                "account_id": "ACC1",
                "symbol": "EURUSD",
                "side": "BUY",
                "order_type": "MARKET",
                "quantity": 1.0,
                "status": "FILLED",
                "submit_time": datetime.utcnow().isoformat()
            }
        ],
        "executions": [
            {
                "execution_id": exec_id,
                "order_id": order_id,
                "run_id": run_id, # API expects it, ingest should strip it
                "strategy_id": "TEST_STRAT_INTEGRATION",
                "account_id": "ACC1",
                "symbol": "EURUSD",
                "side": "BUY",
                "exec_time": datetime.utcnow().isoformat(),
                "price": 1.0500,
                "quantity": 1.0
            }
        ]
    }
    
    resp = client.post("/ingest/stream", json=stream_payload)
    if resp.status_code != 200:
        pytest.fail(f"FAILED to ingest stream: {resp.text}")
        
    resp_data = resp.json()
    print(f"SUCCESS: Stream ingested. Response: {resp_data}")
    
    # 3. Stop Run
    print("\n3. Stopping Run...")
    # No sleep needed for TestClient usually, unless background tasks involved.
    
    resp = client.post(f"/runs/{run_id}/stop")
    if resp.status_code != 200:
        pytest.fail(f"FAILED to stop run: {resp.text}")
        
    run_end_data = resp.json()
    print(f"SUCCESS: Run stopped. Status: {run_end_data.get('status')}, EndTime: {run_end_data.get('end_time')}")
