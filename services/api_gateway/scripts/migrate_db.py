import sqlite3
from datetime import datetime
import uuid
import json
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

DB_PATH = resolve_db_path()

def migrate():
    print(f"Starting migration on {DB_PATH}...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Create new tables
    print("Creating 'strategies' and 'strategy_runs' tables...")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS strategies (
        strategy_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        default_parameters JSON
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS strategy_runs (
        run_id TEXT PRIMARY KEY,
        strategy_id TEXT NOT NULL,
        parameters JSON,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        status TEXT,
        data_range JSON,
        FOREIGN KEY(strategy_id) REFERENCES strategies(strategy_id)
    )
    ''')
    
    # 2. Add run_id column to orders and trades if not exists
    # SQLite doesn't support IF NOT EXISTS for columns, so we try/except
    try:
        cursor.execute("ALTER TABLE orders ADD COLUMN run_id TEXT REFERENCES strategy_runs(run_id)")
        print("Added 'run_id' to 'orders'.")
    except sqlite3.OperationalError:
        print("'run_id' already exists in 'orders'.")
        
    try:
        cursor.execute("ALTER TABLE trades ADD COLUMN run_id TEXT REFERENCES strategy_runs(run_id)")
        print("Added 'run_id' to 'trades'.")
    except sqlite3.OperationalError:
        print("'run_id' already exists in 'trades'.")

    # 3. Migrate existing data
    print("Migrating existing data...")
    
    # Find unique strategies from orders
    cursor.execute("SELECT DISTINCT strategy_id FROM orders WHERE strategy_id IS NOT NULL")
    existing_strategies = cursor.fetchall()
    
    for (strat_id,) in existing_strategies:
        print(f"Processing strategy: {strat_id}")
        
        # Insert Strategy if not exists
        cursor.execute("INSERT OR IGNORE INTO strategies (strategy_id, name) VALUES (?, ?)", (strat_id, strat_id))
        
        # Create a Default Run
        run_id = str(uuid.uuid4())
        print(f"  Creating Default Run: {run_id}")
        
        cursor.execute('''
            INSERT INTO strategy_runs (run_id, strategy_id, start_time, status, parameters)
            VALUES (?, ?, ?, ?, ?)
        ''', (run_id, strat_id, datetime.utcnow(), "COMPLETED", json.dumps({"note": "Legacy Data Migration"})))
        
        # Update Orders
        cursor.execute("UPDATE orders SET run_id = ? WHERE strategy_id = ? AND run_id IS NULL", (run_id, strat_id))
        rows = cursor.rowcount
        print(f"  Linked {rows} orders to run.")
        
        # Update Trades
        cursor.execute("UPDATE trades SET run_id = ? WHERE strategy_id = ? AND run_id IS NULL", (run_id, strat_id))
        rows = cursor.rowcount
        print(f"  Linked {rows} trades to run.")

    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
