import sqlite3

try:
    conn = sqlite3.connect('trading_data.db')
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
