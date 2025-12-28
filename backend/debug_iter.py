
from src.database.connection import SessionLocal
from src.database.models import MlIteration
import json

try:
    db = SessionLocal()
    # Get latest iteration (failed or not)
    obj = db.query(MlIteration).order_by(MlIteration.start_utc.desc()).first()
    
    if obj:
        print(f"ID: {obj.iteration_id}")
        print(f"Status: {obj.status}")
        
        metrics = obj.metrics_json or {}
        print(f"Error: {metrics.get('error')}")
        
        logs = obj.logs_json
        if logs:
            # It might be a string or list
            if isinstance(logs, str):
                try:
                    logs_list = json.loads(logs)
                    print(f"Logs Count: {len(logs_list)}")
                    print("--- LAST 5 LOGS ---")
                    for l in logs_list[-5:]:
                        print(l)
                except:
                    print(f"Raw Logs String (last 200 chars): {logs[-200:]}")
            else:
                print(f"Logs List: {logs[-5:]}")
        else:
            print("Logs: None")
    else:
        print("No iterations found.")
    db.close()
except Exception as e:
    print(f"Script Error: {e}")
