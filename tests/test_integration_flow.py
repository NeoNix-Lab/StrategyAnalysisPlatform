import urllib.request
import urllib.error
import json
import uuid
import time
from datetime import datetime

BASE_URL = "http://127.0.0.1:8000/api"

def make_request(method, endpoint, data=None):
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url, method=method)
    req.add_header('Content-Type', 'application/json')
    
    body = None
    if data:
        body = json.dumps(data).encode('utf-8')
    
    try:
        with urllib.request.urlopen(req, data=body) as response:
            resp_body = response.read().decode('utf-8')
            return json.loads(resp_body)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_flow():
    print("--- Starting Integration Flow Test (urllib) ---")
    
    # 1. Start Run
    print("\n1. Starting Run...")
    start_payload = {
        "strategy_id": "TEST_STRAT_INTEGRATION",
        "parameters": {"param1": 10, "param2": "test"},
        "data_range": {"symbol": "EURUSD", "timeframe": "M1"}
    }
    
    run_data = make_request("POST", "/runs/start", start_payload)
    if not run_data:
        print("FAILED to start run")
        return
    
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
    
    resp_data = make_request("POST", "/ingest/stream", stream_payload)
    if not resp_data:
        print("FAILED to ingest stream")
        return
        
    print(f"SUCCESS: Stream ingested. Response: {resp_data}")
    
    # 3. Stop Run
    print("\n3. Stopping Run...")
    time.sleep(1)
    
    run_end_data = make_request("POST", f"/runs/{run_id}/stop")
    if not run_end_data:
        print("FAILED to stop run")
        return
        
    print(f"SUCCESS: Run stopped. Status: {run_end_data.get('status')}, EndTime: {run_end_data.get('end_time')}")
    
    print("\n--- Integration Test COMPLETED SUCCESSFULY ---")

if __name__ == "__main__":
    test_flow()
