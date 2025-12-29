from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.database.models import MarketSeries, MarketBar

def inspect_market():
    db = SessionLocal()
    
    series_count = db.query(MarketSeries).count()
    bar_count = db.query(MarketBar).count()
    
    print(f"MarketSeries: {series_count}")
    print(f"MarketBars: {bar_count}")
    
    db.close()

if __name__ == "__main__":
    inspect_market()
