import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import engine, Base, SessionLocal
from src.database.models import Bar
from src.etl.import_sqlite import SqliteImporter

def setup_test_db():
    # Use an in-memory DB for testing the logic, but SqliteImporter expects a file path for the source.
    # The destination DB is the main one defined in connection.py. 
    # For safety, let's use a separate test.db for the destination if possible, 
    # but for this quick test we can just use the main DB if we clean up, or mock the session.
    # Let's mock the session to avoid touching the real DB.
    
    # Actually, simpler: Create a temporary SQLite file for the "Source" data.
    pass

def create_source_sqlite(filename, bars_data):
    if os.path.exists(filename):
        os.remove(filename)
        
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    
    # Create Bars table matching the schema expected by importer
    cursor.execute('''
        CREATE TABLE Bars (
            symbol TEXT,
            timeframe TEXT,
            start_time_utc TEXT,
            end_time_utc TEXT,
            open REAL,
            high REAL,
            low REAL,
            close REAL,
            volume REAL,
            open_interest REAL
        )
    ''')
    
    # Create Metadata table
    cursor.execute('CREATE TABLE Metadata (key TEXT, value TEXT)')
    cursor.execute("INSERT INTO Metadata VALUES ('schema_version', '1.0')")
    
    # Create Orders and Executions tables (empty) to avoid errors
    cursor.execute('CREATE TABLE Orders (order_id TEXT)') # Simplified
    cursor.execute('CREATE TABLE Executions (execution_id TEXT)') # Simplified
    
    # Insert data
    for bar in bars_data:
        cursor.execute('''
            INSERT INTO Bars VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', bar)
        
    conn.commit()
    conn.close()

def test_gap_filling():
    # 1. Setup Destination DB (In-Memory for test)
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    test_engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(test_engine)
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    
    importer = SqliteImporter(session)
    
    symbol = "TEST_SYM"
    tf = "1m"
    base_time = datetime(2025, 1, 1, 10, 0, 0)
    
    # 2. Create "Source 1" (Initial Data: 10:00, 10:01)
    # Format: symbol, timeframe, start, end, o, h, l, c, v, oi
    data_1 = [
        (symbol, tf, (base_time + timedelta(minutes=0)).isoformat(), (base_time + timedelta(minutes=1)).isoformat(), 100, 101, 99, 100, 1000, 0),
        (symbol, tf, (base_time + timedelta(minutes=1)).isoformat(), (base_time + timedelta(minutes=2)).isoformat(), 101, 102, 100, 101, 1100, 0)
    ]
    create_source_sqlite('test_source_1.sqlite', data_1)
    
    print("Importing Source 1...")
    importer.import_file('test_source_1.sqlite')
    
    count = session.query(Bar).count()
    print(f"Bars after Import 1: {count} (Expected 2)")
    assert count == 2
    
    # 3. Create "Source 2" (Overlap + New: 10:01, 10:02)
    # Note: 10:01 overlaps. 10:02 is new.
    # IMPORTANT: Change volume of 10:01 to verify it is NOT updated.
    data_2 = [
        (symbol, tf, (base_time + timedelta(minutes=1)).isoformat(), (base_time + timedelta(minutes=2)).isoformat(), 101, 102, 100, 101, 9999, 0), # Modified Volume
        (symbol, tf, (base_time + timedelta(minutes=2)).isoformat(), (base_time + timedelta(minutes=3)).isoformat(), 102, 103, 101, 102, 1200, 0)  # New
    ]
    create_source_sqlite('test_source_2.sqlite', data_2)
    
    print("Importing Source 2...")
    importer.import_file('test_source_2.sqlite')
    
    count = session.query(Bar).count()
    print(f"Bars after Import 2: {count} (Expected 3)")
    assert count == 3
    
    # Verify 10:01 was NOT updated
    bar_1001 = session.query(Bar).filter(Bar.timestamp == base_time + timedelta(minutes=1)).first()
    print(f"Volume of 10:01 Bar: {bar_1001.volume} (Expected 1100, NOT 9999)")
    assert bar_1001.volume == 1100
    
    # 4. Create "Source 3" (Gap: 10:04)
    data_3 = [
        (symbol, tf, (base_time + timedelta(minutes=4)).isoformat(), (base_time + timedelta(minutes=5)).isoformat(), 104, 105, 103, 104, 1400, 0)
    ]
    create_source_sqlite('test_source_3.sqlite', data_3)
    
    print("Importing Source 3...")
    importer.import_file('test_source_3.sqlite')
    
    count = session.query(Bar).count()
    print(f"Bars after Import 3: {count} (Expected 4)")
    assert count == 4
    
    # Cleanup
    session.close()
    test_engine.dispose() # Ensure engine releases locks
    
    import gc
    gc.collect() # Force garbage collection to release file handles
    
    try:
        if os.path.exists('test_source_1.sqlite'): os.remove('test_source_1.sqlite')
        if os.path.exists('test_source_2.sqlite'): os.remove('test_source_2.sqlite')
        if os.path.exists('test_source_3.sqlite'): os.remove('test_source_3.sqlite')
    except PermissionError:
        print("Warning: Could not remove test files due to file lock. Please delete manually.")
    
    print("\n✅ TEST PASSED: Gap filling logic verified.")

if __name__ == "__main__":
    test_gap_filling()
