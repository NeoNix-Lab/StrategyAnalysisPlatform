import sqlite3
import os
from pathlib import Path

# Logic to find DB similar to connection.py
DB_PATH = os.getenv("TRADING_DB_PATH")
if not DB_PATH:
    current_file = Path(__file__).resolve()
    # scripts -> Main
    project_root = current_file.parents[1]
    
    var_db = project_root / "var" / "trading_data.db"
    root_db = project_root / "trading_data.db"
    
    if var_db.exists():
        DB_PATH = str(var_db)
    elif root_db.exists():
        DB_PATH = str(root_db)
    else:
        # Fallback
        DB_PATH = "trading_data.db"

print(f"Migrating Database at: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

tables_to_migrate = [
    "strategies",
    "strategy_instances",
    "datasets",
    "ml_reward_functions",
    "ml_model_architectures",
    "ml_training_processes",
    "ml_training_sessions"
]

for table in tables_to_migrate:
    print(f"Checking {table}...")
    try:
        # Check if column exists
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in cursor.fetchall()]
        
        if "user_id" not in columns:
            print(f"Adding user_id to {table}...")
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN user_id VARCHAR")
        else:
            print(f"user_id already exists in {table}.")
            
    except Exception as e:
        print(f"Error checking/migrating {table}: {e}")

conn.commit()
conn.close()
print("Migration completed.")
