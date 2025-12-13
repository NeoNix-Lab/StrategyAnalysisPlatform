from src.database.connection import get_db
from src.database.models import Trade, Order, StrategyRun, Side
import uuid
from datetime import datetime, timedelta
import random

db = next(get_db())

# Check current state
runs = db.query(StrategyRun).all()
print(f"Found {len(runs)} runs:")
for run in runs:
    trades_count = db.query(Trade).filter(Trade.run_id == run.run_id).count()
    orders_count = db.query(Order).filter(Order.run_id == run.run_id).count()
    print(f"  Run {run.run_id[:8]}... ({run.strategy_id}): {trades_count} trades, {orders_count} orders")

# Generate dummy trades for each run
print("\nGenerating dummy trades...")

for run in runs:
    # Check if already has trades
    existing_trades = db.query(Trade).filter(Trade.run_id == run.run_id).count()
    if existing_trades > 0:
        print(f"  Run {run.run_id[:8]} already has {existing_trades} trades, skipping...")
        continue
    
    # Generate 50 random trades
    num_trades = 50
    start_date = run.start_time if run.start_time else datetime(2024, 1, 1)
    
    cumulative_pnl = 0
    
    for i in range(num_trades):
        # Random trade parameters
        side = random.choice([Side.BUY, Side.SELL])
        entry_time = start_date + timedelta(hours=i * 2)
        exit_time = entry_time + timedelta(minutes=random.randint(15, 240))
        
        entry_price = 50000 + random.uniform(-5000, 5000)
        exit_price = entry_price * (1 + random.uniform(-0.02, 0.03))
        
        quantity = random.uniform(0.01, 0.1)
        
        # Calculate PnL
        if side == Side.BUY:
            pnl_gross = (exit_price - entry_price) * quantity
        else:
            pnl_gross = (entry_price - exit_price) * quantity
        
        commission = quantity * entry_price * 0.0004  # 0.04% commission
        pnl_net = pnl_gross - commission
        
        cumulative_pnl += pnl_net
        
        # MAE and MFE (random for now)
        mae = abs(pnl_gross) * random.uniform(0.3, 0.8) * -1
        mfe = abs(pnl_gross) * random.uniform(1.2, 2.0)
        
        duration_seconds = (exit_time - entry_time).total_seconds()
        
        # Random regime
        regime_trend = random.choice(["BULL", "BEAR", "RANGE"])
        regime_volatility = random.choice(["HIGH", "LOW", "NORMAL"])
        setup_tag = random.choice(["Breakout", "Pullback", "Reversal", "Continuation"])
        
        trade = Trade(
            trade_id=str(uuid.uuid4()),
            run_id=run.run_id,
            strategy_id=run.strategy_id,
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
    
    print(f"  Generated {num_trades} trades for run {run.run_id[:8]}... (Total PnL: {cumulative_pnl:.2f})")

db.commit()
print("\nDone! Database populated with dummy trades.")

# Verify
print("\nFinal state:")
for run in runs:
    trades_count = db.query(Trade).filter(Trade.run_id == run.run_id).count()
    orders_count = db.query(Order).filter(Order.run_id == run.run_id).count()
    print(f"  Run {run.run_id[:8]}... ({run.strategy_id}): {trades_count} trades, {orders_count} orders")
