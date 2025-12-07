import sqlite3
import os

DB_PATH = "trading_data.db"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file {DB_PATH} not found!")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check Strategies
    cursor.execute("SELECT count(*) FROM strategies")
    strategies_count = cursor.fetchone()[0]
    print(f"Strategies: {strategies_count}")
    
    if strategies_count > 0:
        cursor.execute("SELECT * FROM strategies")
        print("Strategies Data:", cursor.fetchall())

    # Check Orders
    cursor.execute("SELECT count(*) FROM orders")
    orders_count = cursor.fetchone()[0]
    print(f"Orders: {orders_count}")
    
    # Check Strategy Runs
    cursor.execute("SELECT count(*) FROM strategy_runs")
    runs_count = cursor.fetchone()[0]
    print(f"Strategy Runs: {runs_count}")

    conn.close()

if __name__ == "__main__":
    check_db()
