from src.database.connection import get_db
from src.database.models import Trade, StrategyRun, Side
import uuid
from datetime import datetime, timedelta
import random

db = next(get_db())

# Fix the run with None start_time
run_with_null = db.query(StrategyRun).filter(StrategyRun.run_id == '81e7d05f-b72d-40b1-adcd-57ccad33c416').first()
if run_with_null and run_with_null.start_time is None:
    run_with_null.start_time = datetime(2024, 11, 15, 10, 0, 0)
    run_with_null.end_time = datetime(2024, 12, 1, 18, 30, 0)
    print(f"Updated run {run_with_null.run_id[:8]} start_time to {run_with_null.start_time}")

# Add more trades to the first run (b34c1ef2) to have at least 50 trades
run_first = db.query(StrategyRun).filter(StrategyRun.run_id == 'b34c1ef2-7c84-41df-9579-4b7e67aaceab').first()
if run_first:
    current_trades = db.query(Trade).filter(Trade.run_id == run_first.run_id).count()
    trades_to_add = max(0, 50 - current_trades)
    
    if trades_to_add > 0:
        print(f"\nAdding {trades_to_add} more trades to run {run_first.run_id[:8]}...")
        
        start_date = run_first.start_time if run_first.start_time else datetime(2024, 1, 1)
        
        for i in range(trades_to_add):
            side = random.choice([Side.BUY, Side.SELL])
            entry_time = start_date + timedelta(hours=(current_trades + i) * 2)
            exit_time = entry_time + timedelta(minutes=random.randint(15, 240))
            
            entry_price = 50000 + random.uniform(-5000, 5000)
            exit_price = entry_price * (1 + random.uniform(-0.02, 0.03))
            
            quantity = random.uniform(0.01, 0.1)
            
            if side == Side.BUY:
                pnl_gross = (exit_price - entry_price) * quantity
            else:
                pnl_gross = (entry_price - exit_price) * quantity
            
            commission = quantity * entry_price * 0.0004
            pnl_net = pnl_gross - commission
            
            mae = abs(pnl_gross) * random.uniform(0.3, 0.8) * -1
            mfe = abs(pnl_gross) * random.uniform(1.2, 2.0)
            duration_seconds = (exit_time - entry_time).total_seconds()
            
            regime_trend = random.choice(["BULL", "BEAR", "RANGE"])
            regime_volatility = random.choice(["HIGH", "LOW", "NORMAL"])
            setup_tag = random.choice(["Breakout", "Pullback", "Reversal", "Continuation"])
            
            trade = Trade(
                trade_id=str(uuid.uuid4()),
                run_id=run_first.run_id,
                strategy_id=run_first.strategy_id,
                symbol="BTCUSDT",
                side=side,
                entry_time=entry_time,
                exit_time=exit_time,
                entry_price=entry_price,
                exit_price=exit_price,
                quantity=quantity,
                pnl_gross=pnl_gross,
                pnl_net=pnl_net,
                commission=commission,
                mae=mae,
                mfe=mfe,
                duration_seconds=duration_seconds,
                regime_trend=regime_trend,
                regime_volatility=regime_volatility,
                setup_tag=setup_tag
            )
            
            db.add(trade)
        
        print(f"Added {trades_to_add} trades to run {run_first.run_id[:8]}")

db.commit()
print("\nDatabase updated successfully!")

# Verify final state
print("\nFinal state:")
runs = db.query(StrategyRun).all()
for run in runs:
    trades_count = db.query(Trade).filter(Trade.run_id == run.run_id).count()
    print(f"  Run {run.run_id[:8]}... ({run.start_time}): {trades_count} trades")
