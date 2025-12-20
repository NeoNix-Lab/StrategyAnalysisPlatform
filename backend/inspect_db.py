from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.database.models import Trade, Bar, RunSeries, StrategyRun

def inspect():
    db = SessionLocal()
    
    run_count = db.query(StrategyRun).count()
    series_count = db.query(RunSeries).count()
    bar_count = db.query(Bar).count()
    trade_count = db.query(Trade).count()
    
    print(f"Runs: {run_count}")
    print(f"Series: {series_count}")
    print(f"Bars: {bar_count}")
    print(f"Trades: {trade_count}")
    
    if series_count > 0:
        first_series = db.query(RunSeries).first()
        print(f"First Series: {first_series.series_id} (Run: {first_series.run_id}) | Bars: {len(first_series.bars)}")
        
    db.close()

if __name__ == "__main__":
    inspect()
