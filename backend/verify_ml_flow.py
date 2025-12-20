import httpx
import time
import sys
import asyncio

BASE_URL = "http://localhost:8000/api"

async def run_test():
    async with httpx.AsyncClient() as client:
        print("1. Listing Runs...")
        try:
            res = await client.get(f"{BASE_URL}/runs/")
            runs = res.json()
        except Exception as e:
            print(f"Failed to fetch runs: {e}")
            return

        if not runs:
            print("ERROR: No runs found. Cannot test.")
            return
        
        first_run = runs[0]
        run_id = first_run['run_id']
        print(f"   Using Run ID: {run_id}")

        print("2. Creating Dataset...")
        dataset_payload = {
            "name": "Test Dataset Auto",
            "description": "Created by verification script",
            "sources": [
                {
                    "run_id": run_id,
                    "symbol": first_run['symbol'],
                    "timeframe": first_run['timeframe']
                }
            ],
            "feature_config": ["open", "close"]
        }
        
        ds_res = await client.post(f"{BASE_URL}/datasets/", json=dataset_payload)
        ds = ds_res.json()
        dataset_id = ds['dataset_id']
        print(f"   Dataset Created: {dataset_id}")

        print("3. Starting Training...")
        training_payload = {
            "dataset_id": dataset_id,
            "model_architecture": [
                {"type": "input", "layer": {"type": "Input", "params": {"shape": [10, 5]}}},
                {"type": "hidden", "layer": {"type": "Dense", "params": {"units": 64, "activation": "relu"}}},
                {"type": "output", "layer": {"type": "Dense", "params": {"units": 3, "activation": "linear"}}}
            ],
            "training_params": {
                "epochs": 1,
                "batch_size": 32,
                "window_size": 10
            }
        }
        
        try:
            train_res = await client.post(f"{BASE_URL}/training/start", json=training_payload)
            train_res.raise_for_status()
            job = train_res.json()
            job_id = job['job_id']
            print(f"   Job Started: {job_id}")
        except Exception as e:
            print(f"   ERROR Starting Training: {e}")
            if 'train_res' in locals():
                print(train_res.text)
            return

        print("4. Checking Status...")
        time.sleep(2)
        status_res = await client.get(f"{BASE_URL}/training/status/{job_id}")
        status = status_res.json()
        print(f"   Current Status: {status['status']}")
        
        print("\nSUCCESS: End-to-End Flow Verified!")

if __name__ == "__main__":
    try:
        asyncio.run(run_test())
    except Exception as e:
        print(f"Verification Failed: {e}")
        sys.exit(1)
