import sqlite3
import os
from pathlib import Path

def resolve_db_path() -> str:
    env_path = os.getenv("TRADING_DB_PATH")
    if env_path:
        return env_path
    project_root = Path(__file__).resolve().parents[3]
    var_db = project_root / "var" / "trading_data.db"
    if var_db.exists():
        return str(var_db)
    return str(project_root / "trading_data.db")

try:
    conn = sqlite3.connect(resolve_db_path())
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r[0] for r in cursor.fetchall()]
    print(f"Tables: {tables}")
    
    required = ['users', 'user_settings', 'api_keys']
    missing = [t for t in required if t not in tables]
    
    if missing:
        print(f"Missing tables: {missing}")
        exit(1) # Fail if missing
    else:
        print("All Auth tables present.")
        exit(0)
except Exception as e:
    print(e)
    exit(1)
