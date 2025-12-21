
import uuid
import json
from datetime import datetime, timedelta
import random
from src.database.connection import SessionLocal, init_db
from src.database.models import Dataset, RunSeries, Bar, StrategyRun, StrategyInstance, RunType

def seed_dataset():
    init_db()
    db = SessionLocal()
    
    # Ensure there is a dummy Run and Series to point to
    # Check if any run exists
    run = db.query(StrategyRun).first()
    if not run:
        print("Creating dummy Strategy Run for Dataset source...")
        # Need Instance first
        instance = StrategyInstance(
            instance_id=str(uuid.uuid4()),
            strategy_id="dummy-strategy", # assuming no FK constraint or string
            parameters_json={},
            symbol="BTC-USDT"
        )
        db.add(instance)
        
        run = StrategyRun(
            run_id=str(uuid.uuid4()),
            instance_id=instance.instance_id,
            run_type=RunType.BACKTEST,
            start_utc=datetime.utcnow(),
            status="COMPLETED"
        )
        db.add(run)
        
        series = RunSeries(
            series_id=str(uuid.uuid4()),
            run_id=run.run_id,
            symbol="BTC-USDT",
            timeframe="1h"
        )
        db.add(series)
        
        # Add some Dummy Bars
        start_time = datetime.utcnow() - timedelta(days=5)
        price = 50000.0
        for i in range(1000): # 1000 hours
            price += random.uniform(-100, 100)
            bar = Bar(
                series_id=series.series_id,
                ts_utc=start_time + timedelta(hours=i),
                open=price,
                high=price + 50,
                low=price - 50,
                close=price + 10,
                volume=random.uniform(10, 100)
            )
            db.add(bar)
            
        print(f"Created 1000 dummy bars for run {run.run_id}")
        db.commit()
    else:
        # Use existing run
        pass
        
    # Now Create Dataset
    # Find a valid run
    run = db.query(StrategyRun).first()
    dataset = Dataset(
        dataset_id=str(uuid.uuid4()),
        name="BTC-USDT-1h-2024 (Simulated)",
        description="A simulated dataset for testing ML training flow.",
        sources_json=[{"run_id": run.run_id}],
        feature_config_json=["open", "close", "rsi", "macd"]
    )
    
    db.add(dataset)
    db.commit()
    print(f"Seeded Dataset: {dataset.name}")
    db.close()

if __name__ == "__main__":
    seed_dataset()
