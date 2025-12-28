
import sys
import os
import uvicorn
from sqlalchemy.orm import Session

# Add current dir to path
sys.path.append(os.getcwd())

from src.database.connection import SessionLocal
from src.database.models import MlRewardFunction

def update_legacy_metadata():
    db: Session = SessionLocal()
    try:
        # Find the function
        func = db.query(MlRewardFunction).filter(MlRewardFunction.name == "Legacy Strategy (Modernized)").first()
        if not func:
            print("Legacy Strategy not found.")
            return

        print(f"Updating metadata for: {func.name}")
        
        # Explicitly define standard labels
        func.metadata_json = {
            "action_labels": ["HOLD", "BUY", "SELL"],
            "status_labels": ["FLAT", "LONG", "SHORT"]
        }
        
        db.commit()
        print("Metadata updated successfully.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    update_legacy_metadata()
