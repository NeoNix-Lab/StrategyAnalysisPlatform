import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.database.connection import engine, Base, SessionLocal
from src.database.models import Bar, Order, StrategyRun, Strategy, Side, OrderType, OrderStatus
from src.etl.import_sqlite import SqliteImporter

def create_source_sqlite(filename):
    if os.path.exists(filename):
        os.remove(filename)
        
    conn = sqlite3.connect(filename)
    cursor = conn.cursor()
    
    # Create Tables
    cursor.execute('CREATE TABLE Metadata (key TEXT, value TEXT)')
    cursor.execute("INSERT INTO Metadata VALUES ('schema_version', '1.0')")
    
    cursor.execute('''
        CREATE TABLE Bars (
            symbol TEXT, timeframe TEXT, start_time_utc TEXT, end_time_utc TEXT, 
            open REAL, high REAL, low REAL, close REAL, volume REAL, open_interest REAL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE Orders (
            order_id TEXT, parent_order_id TEXT, strategy_id TEXT, strategy_version TEXT,
            account_id TEXT, symbol TEXT, side TEXT, order_type TEXT, time_in_force TEXT,
            submit_time_utc TEXT, price REAL, stop_price REAL, quantity REAL, status TEXT,
            reject_reason TEXT, cancel_reason TEXT, client_tag TEXT, meta_json TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE Executions (
            execution_id TEXT, order_id TEXT, strategy_id TEXT, account_id TEXT, symbol TEXT,
            side TEXT, exec_time_utc TEXT, price REAL, quantity REAL, fee REAL, 
            fee_currency TEXT, liquidity_flag TEXT
        )
    ''')
    
    # Insert Dummy Order
    cursor.execute('''
        INSERT INTO Orders VALUES (
            'ORD-001', NULL, 'TEST_STRAT', '1.0', 'ACC-1', 'EURUSD', 'BUY', 'MARKET', 'GTC',
            '2025-01-01 10:00:00', 1.1000, NULL, 1.0, 'FILLED', NULL, NULL, NULL, NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def test_strategy_run_import():
    # 1. Setup DB
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    test_engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(test_engine)
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    
    importer = SqliteImporter(session)
    
    # 2. Create Source File
    source_file = 'test_run_import.sqlite'
    create_source_sqlite(source_file)
    
    # 3. Import
    print("Running Import...")
    importer.import_file(source_file)
    
    # 4. Verify Strategy Created
    strat = session.query(Strategy).filter_by(strategy_id='TEST_STRAT').first()
    assert strat is not None
    print(f"✅ Strategy Created: {strat.name}")
    
    # 5. Verify Run Created
    run = session.query(StrategyRun).filter_by(strategy_id='TEST_STRAT').first()
    assert run is not None
    print(f"✅ Run Created: {run.run_id}")
    
    # 6. Verify Order Linked to Run
    order = session.query(Order).filter_by(order_id='ORD-001').first()
    assert order.run_id == run.run_id
    print(f"✅ Order Linked to Run: {order.run_id}")
    
    # Cleanup
    session.close()
    test_engine.dispose()
    if os.path.exists(source_file):
        try:
            os.remove(source_file)
        except:
            pass
            
    print("\n✅ TEST PASSED: Strategy Run logic verified.")

if __name__ == "__main__":
    test_strategy_run_import()
