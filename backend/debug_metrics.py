
import sys
import os

# Add src to path
sys.path.append(os.getcwd())

from src.database.connection import SessionLocal
from src.services.analytics import StandardAnalyzer
import traceback

def test_metrics(run_id):
    db = SessionLocal()
    try:
        print(f"Testing metrics for Run ID: {run_id}")
        analyzer = StandardAnalyzer(db)
        metrics = analyzer.calculate_portfolio_metrics(run_id=run_id)
        print("Metrics calculated successfully:")
        print(metrics)
        
        import json
        print("Testing JSON Serialization...")
        # FastAPI might fail on numpy types if not handled
        json.dumps(metrics) 
        print("JSON Serialization SUCCESS")
    except TypeError as te:
        print(f"JSON Serialization FAILED: {te}")
    except Exception as e:
        print("CRASHED:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    # Use the ID from the logs: 758c4c9b-fb58-41ac-bd5b-1bab64210107
    # Or just grab the last run
    run_id = "758c4c9b-fb58-41ac-bd5b-1bab64210107"
    if len(sys.argv) > 1:
        run_id = sys.argv[1]
    
    test_metrics(run_id)
