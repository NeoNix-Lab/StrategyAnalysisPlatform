from src.database.connection import SessionLocal
from src.database.models import Dataset, MarketSeries, MarketBar
from datetime import datetime, timedelta
import numpy as np
import uuid
import sys

sys.stdout.reconfigure(encoding='utf-8')

def generate_dummy_data(series_id, start_time, steps=1000, start_price=50000.0):
    bars = []
    price = start_price
    current_time = start_time
    
    print(f"Generating {steps} bars for series {series_id}...")
    
    for i in range(steps):
        change = np.random.normal(0, price * 0.001) # 0.1% volatility
        open_p = price
        close_p = price + change
        high_p = max(open_p, close_p) + abs(np.random.normal(0, price * 0.0005))
        low_p = min(open_p, close_p) - abs(np.random.normal(0, price * 0.0005))
        volume = abs(np.random.normal(100, 50))
        
        bar = MarketBar(
            series_id=series_id,
            ts_utc=current_time,
            open=open_p,
            high=high_p,
            low=low_p,
            close=close_p,
            volume=volume
        )
        bars.append(bar)
        
        price = close_p
        current_time += timedelta(minutes=1)
        
    return bars

def populate_datasets():
    db = SessionLocal()
    datasets = db.query(Dataset).all()
    
    for ds in datasets:
        print(f"Checking Dataset: {ds.name} ({ds.dataset_id})")
        sources = ds.sources_json or []
        
        # If no sources, define a default one
        if not sources:
            print("  No sources defined. Adding default BTC/USDT source.")
            sources = [{
                "symbol": "BTC/USDT",
                "timeframe": "1m",
                "venue": "Binance",
                "provider": "Dummy"
            }]
            ds.sources_json = sources
            db.commit()
            
        is_empty = True
        
        for source in sources:
            symbol = source.get("symbol", "BTC/USDT")
            tf = source.get("timeframe", "1m")
            venue = source.get("venue", "Binance")
            provider = source.get("provider", "Dummy")
            
            # Find or Create MarketSeries
            series = db.query(MarketSeries).filter(
                MarketSeries.symbol == symbol,
                MarketSeries.timeframe == tf,
                MarketSeries.venue == venue,
                MarketSeries.provider == provider
            ).first()
            
            if not series:
                print(f"  Creating new MarketSeries for {symbol} {tf}...")
                series = MarketSeries(
                    series_id=str(uuid.uuid4()),
                    symbol=symbol,
                    timeframe=tf,
                    venue=venue,
                    provider=provider
                )
                db.add(series)
                db.commit()
                
            # Check for data
            count = db.query(MarketBar).filter(MarketBar.series_id == series.series_id).count()
            print(f"  Series {symbol} has {count} bars.")
            
            if count == 0:
                # Generate Data
                bars = generate_dummy_data(series.series_id, datetime.utcnow() - timedelta(minutes=1000))
                db.bulk_save_objects(bars)
                db.commit()
                print(f"  Added {len(bars)} dummy bars.")
            else:
                is_empty = False
                
    db.close()
    print("Done.")

if __name__ == "__main__":
    populate_datasets()
