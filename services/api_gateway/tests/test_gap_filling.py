import sqlite3
import pytest
from datetime import datetime, timedelta
import os
from quant_shared.models.models import RunSeriesBar as Bar
from etl.import_sqlite import SqliteImporter

def create_source_sqlite(path, bars_data):
    if os.path.exists(path):
        os.remove(path)
        
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Create Tables
    cursor.execute('''
        CREATE TABLE Bars (
            symbol TEXT, timeframe TEXT, start_time_utc TEXT, end_time_utc TEXT, 
            open REAL, high REAL, low REAL, close REAL, volume REAL, open_interest REAL
        )
    ''')
    
    cursor.execute('CREATE TABLE Metadata (key TEXT, value TEXT)')
    cursor.execute("INSERT INTO Metadata VALUES ('schema_version', '1.0')")
    cursor.execute('CREATE TABLE Orders (order_id TEXT)') 
    cursor.execute('CREATE TABLE Executions (execution_id TEXT)')
    
    for bar in bars_data:
        cursor.execute('''
            INSERT INTO Bars VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', bar)
        
    conn.commit()
    conn.close()

def test_gap_filling(db_session, tmp_path):
    pytest.skip("SqliteImporter is disabled in V2 architecture")
    importer = SqliteImporter(db_session)
    
    symbol = "TEST_SYM"
    tf = "1m"
    base_time = datetime(2025, 1, 1, 10, 0, 0)
    
    # 2. Create "Source 1" (Initial Data: 10:00, 10:01)
    data_1 = [
        (symbol, tf, (base_time + timedelta(minutes=0)).isoformat(), (base_time + timedelta(minutes=1)).isoformat(), 100, 101, 99, 100, 1000, 0),
        (symbol, tf, (base_time + timedelta(minutes=1)).isoformat(), (base_time + timedelta(minutes=2)).isoformat(), 101, 102, 100, 101, 1100, 0)
    ]
    source_1 = tmp_path / 'test_source_1.sqlite'
    create_source_sqlite(str(source_1), data_1)
    
    print("Importing Source 1...")
    importer.import_file(str(source_1))
    
    count = db_session.query(Bar).count()
    assert count == 2
    
    # 3. Create "Source 2" (Overlap + New: 10:01, 10:02)
    data_2 = [
        (symbol, tf, (base_time + timedelta(minutes=1)).isoformat(), (base_time + timedelta(minutes=2)).isoformat(), 101, 102, 100, 101, 9999, 0), # Modified Volume
        (symbol, tf, (base_time + timedelta(minutes=2)).isoformat(), (base_time + timedelta(minutes=3)).isoformat(), 102, 103, 101, 102, 1200, 0)  # New
    ]
    source_2 = tmp_path / 'test_source_2.sqlite'
    create_source_sqlite(str(source_2), data_2)
    
    print("Importing Source 2...")
    importer.import_file(str(source_2))
    
    count = db_session.query(Bar).count()
    assert count == 3
    
    # Verify 10:01 was NOT updated
    bar_1001 = db_session.query(Bar).filter(Bar.ts_utc == base_time + timedelta(minutes=1)).first()
    assert bar_1001.volume == 1100
    
    # 4. Create "Source 3" (Gap: 10:04)
    data_3 = [
        (symbol, tf, (base_time + timedelta(minutes=4)).isoformat(), (base_time + timedelta(minutes=5)).isoformat(), 104, 105, 103, 104, 1400, 0)
    ]
    source_3 = tmp_path / 'test_source_3.sqlite'
    create_source_sqlite(str(source_3), data_3)
    
    print("Importing Source 3...")
    importer.import_file(str(source_3))
    
    count = db_session.query(Bar).count()
    assert count == 4
