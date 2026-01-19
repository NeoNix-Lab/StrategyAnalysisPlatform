
import sys
import os
import sqlite3
from pathlib import Path

# Add project root to path to import quant_shared if needed, 
# but for raw SQLite migration we might just need the path.
# We will use the logic from connection.py to resolve the path if possible, 
# or just look for trading_data.db in likely locations.

def find_db_path():
    # Mirrored logic from connection.py
    # 1. Env
    db_path = os.getenv("TRADING_DB_PATH")
    if db_path and os.path.exists(db_path):
        return db_path
        
    # 2. Heuristics
    current_dir = Path(__file__).resolve().parent # scripts/
    root = current_dir.parent # Main/
    
    candidates = [
        root / "trading_data.db",
        root / "var" / "trading_data.db",
        root / "quant.db" # Seen in file list
    ]
    
    for c in candidates:
        if c.exists():
            return str(c)
            
    return None

def migrate():
    db_path = find_db_path()
    if not db_path:
        print("Error: Could not find database file.")
        sys.exit(1)
        
    print(f"Migrating database at: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # helper to check column existence
    def column_exists(table, col):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [info[1] for info in cursor.fetchall()]
        return col in columns
    
    table_name = "ml_training_processes"
    
    # 1. decay_function
    if not column_exists(table_name, "decay_function"):
        print("Adding column decay_function...")
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN decay_function TEXT DEFAULT 'LINEAR'")
        except Exception as e:
            print(f"Error adding decay_function: {e}")
    else:
        print("Column decay_function already exists.")

    # 2. decay_scope
    if not column_exists(table_name, "decay_scope"):
        print("Adding column decay_scope...")
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN decay_scope TEXT DEFAULT 'GLOBAL'")
        except Exception as e:
             print(f"Error adding decay_scope: {e}")
    else:
        print("Column decay_scope already exists.")

    # 3. force_decay_steps
    if not column_exists(table_name, "force_decay_steps"):
        print("Adding column force_decay_steps...")
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN force_decay_steps INTEGER DEFAULT NULL")
        except Exception as e:
             print(f"Error adding force_decay_steps: {e}")
    else:
        print("Column force_decay_steps already exists.")
        
    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
