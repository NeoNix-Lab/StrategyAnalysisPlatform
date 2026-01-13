import sqlite3
import os
from pathlib import Path

def resolve_db_path() -> str:
    env_path = os.getenv("TRADING_DB_PATH")
    if env_path:
        return env_path
    project_root = Path(__file__).resolve().parents[1]
    var_db = project_root / "var" / "trading_data.db"
    if var_db.exists():
        return str(var_db)
    return str(project_root / "trading_data.db")

DB_PATH = resolve_db_path()

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found at {DB_PATH}")
        return

    print(f"🔍 Checking database: {DB_PATH}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Get all table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        all_tables = [row[0] for row in cursor.fetchall()]
        print(f"\n📂 Existing Tables: {', '.join(all_tables)}")

        # Check Specific Tables
        target_tables = [
            "strategy_runs", 
            "strategies", 
            "strategy_instances",
            "executions", 
            "trades",
            "bars",
            "market_bars",
            "ml_training_sessions",
            "ml_iterations"
        ]
        
        print("\n📊 Table Counts:")
        for table in target_tables:
            if table in all_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   - {table}: {count:,} records")
            else:
                print(f"   - {table}: ⚠️ Not Found")

        conn.close()

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    check_db()
