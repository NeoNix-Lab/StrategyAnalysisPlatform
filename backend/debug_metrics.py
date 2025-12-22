from src.database.connection import SessionLocal
from src.database.models import MlIteration
import json
import sys

# Ensure we can print utf-8
sys.stdout.reconfigure(encoding='utf-8')

db = SessionLocal()
iterations = db.query(MlIteration).filter(MlIteration.status == "RUNNING").all()

print(f"Found {len(iterations)} running iterations.")

for iter in iterations:
    print(f"Iteration: {iter.iteration_id}")
    print(f"Metrics JSON Type: {type(iter.metrics_json)}")
    try:
        # Dump to string to see exact content
        print("Metrics JSON Content:")
        print(json.dumps(iter.metrics_json, indent=2))
    except Exception as e:
        print(f"Error dumping json: {e}")
        print(f"Raw content: {iter.metrics_json}")
    
db.close()
