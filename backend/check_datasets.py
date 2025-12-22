from src.database.connection import SessionLocal
from src.database.models import Dataset, RunSeries, Bar, MarketSeries, MarketBar
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def check_datasets():
    db = SessionLocal()
    datasets = db.query(Dataset).all()
    
    print(f"Found {len(datasets)} datasets.")
    print("-" * 60)
    
    empty_datasets = []
    
    for ds in datasets:
        print(f"Dataset: {ds.name} (ID: {ds.dataset_id})")
        sources = ds.sources_json or []
        total_bars = 0
        
        if not sources:
            print("  [WARNING] No sources defined in sources_json.")
        
        for source in sources:
            symbol = source.get("symbol")
            tf = source.get("timeframe")
            run_id = source.get("run_id")
            
            # Check RunSeries/Bar
            if run_id:
                series = db.query(RunSeries).filter(
                    RunSeries.run_id == run_id,
                    RunSeries.symbol == symbol,
                    RunSeries.timeframe == tf
                ).first()
                if series:
                    count = db.query(Bar).filter(Bar.series_id == series.series_id).count()
                    print(f"  Source (Run): {symbol} {tf} -> {count} bars")
                    total_bars += count
                else:
                    print(f"  Source (Run): {symbol} {tf} -> Series not found")
            
            # Check MarketSeries/MarketBar (implied if run_id is missing or generic)
            else:
                m_series = db.query(MarketSeries).filter(
                    MarketSeries.symbol == symbol,
                    MarketSeries.timeframe == tf
                ).first()
                if m_series:
                    count = db.query(MarketBar).filter(MarketBar.series_id == m_series.series_id).count()
                    print(f"  Source (Market): {symbol} {tf} -> {count} bars")
                    total_bars += count
                else:
                    print(f"  Source (Market): {symbol} {tf} -> Series not found")

        if total_bars == 0:
            print("  => IS EMPTY")
            empty_datasets.append(ds.dataset_id)
        else:
            print(f"  => Total Bars: {total_bars}")
        print("-" * 60)
        
    db.close()
    return empty_datasets

if __name__ == "__main__":
    check_datasets()
