import sqlite3
import os

DB_PATH = "trading_data.db"

def check_db():
    if not os.path.exists(DB_PATH):
        print(f"❌ Database file not found at {DB_PATH}")
        return

    print(f"🔍 Checking database: {DB_PATH}")
    print(f"   Size: {os.path.getsize(DB_PATH) / (1024*1024):.2f} MB")

    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. Integrity Check
        print("\n⚙️ Running PRAGMA integrity_check...")
        cursor.execute("PRAGMA integrity_check;")
        result = cursor.fetchone()
        if result[0] == "ok":
            print("✅ Integrity Check Passed.")
        else:
            print(f"❌ Integrity Check Failed: {result}")

        # 2. Key Tables Statistics
        print("\n📊 Table Statistics (Recoverable Data):")
        tables = ["executions", "bars", "trades", "runs", "setups"]
        
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"   - {table}: {count:,} records")
            except sqlite3.OperationalError:
                print(f"   - {table}: ⚠️ Table not found")

        conn.close()

    except Exception as e:
        print(f"\n❌ Critical Error: {str(e)}")

if __name__ == "__main__":
    check_db()
