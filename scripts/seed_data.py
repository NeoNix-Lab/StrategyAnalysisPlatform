
import random
from datetime import datetime, timedelta
import uuid
import json

from sqlalchemy.orm import Session
from sqlalchemy import func
from quant_shared.models.connection import get_db, init_db, engine
from quant_shared.models.models import (
    Strategy, StrategyInstance, StrategyRun, Trade, Execution, Order,
    Dataset, MlRewardFunction, MlModelArchitecture, MlTrainingProcess, 
    MlTrainingSession, MlIteration, OrderOcoGroup, RunSeries, RunSeriesRunLink, RunSeriesBar,
    RunType, RunStatus, Side, OrderType, OrderStatus, PositionImpactType,
    Base
)

def create_dummy_data():
    print("🚀 Initializing DB...")
    init_db()
    
    db = next(get_db())
    
    try:
        # --- 0. Setup Time Anchors ---
        # Everything relative to NOW
        now_utc = datetime.utcnow()
        # Bars cover last 30 days
        data_start_utc = now_utc - timedelta(days=30)
        data_end_utc = now_utc

        # --- 1. Create Strategies ---
        print("Creating Strategies...")
        strategies = [
            Strategy(
                strategy_id=str(uuid.uuid4()),
                name="TrendFollower Alpha",
                version="1.0.2",
                vendor="QuantLab",
                notes="Standard moving average crossover",
                parameters_json=[
                    {"name": "fast_ma", "default_value": 12, "type_hint": "integer", "required": True},
                    {"name": "slow_ma", "default_value": 26, "type_hint": "integer", "required": True}
                ]
            ),
            Strategy(
                strategy_id=str(uuid.uuid4()),
                name="MeanReversion X",
                version="2.1.0",
                vendor="External",
                notes="Bollinger bands strategy",
                parameters_json=[
                    {"name": "lookback", "default_value": 20, "type_hint": "integer", "required": True},
                    {"name": "std_dev", "default_value": 2.0, "type_hint": "number", "required": True}
                ]
            ),
             Strategy(
                strategy_id=str(uuid.uuid4()),
                name="DeepRL Trader",
                version="0.5.0-beta",
                vendor="AI Lab",
                notes="PPO agent trained on BTCUSDT",
                parameters_json=[
                    {"name": "epsilon_start", "default_value": 1.0, "type_hint": "number", "required": True}
                ]
            )
        ]
        
        # Upsert strategies
        final_strategies = []
        for s in strategies:
            exists = db.query(Strategy).filter_by(name=s.name).first()
            if not exists:
                db.add(s)
                final_strategies.append(s)
            else:
                final_strategies.append(exists)
        db.commit()


        # --- 2. Create Market Data Series (The Foundation) ---
        print("Creating Market Data Series & Bars...")
        
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        timeframes = ["1m", "5m", "1h"]
        
        # Store created series to link later
        # Key: (symbol, timeframe) -> RunSeries object
        series_registry = {}
        
        for symbol in symbols:
            for tf in timeframes:
                series_id = f"{symbol}_{tf}_shared"
                
                # Check/Create Series
                series = db.query(RunSeries).filter_by(series_id=series_id).first()
                if not series:
                    series = RunSeries(
                        series_id=series_id,
                        symbol=symbol,
                        timeframe=tf,
                        venue="Binance",
                        provider="Quantower",
                        start_utc=data_start_utc,
                        end_utc=data_end_utc,
                        created_utc=now_utc
                    )
                    db.add(series)
                    print(f"+ Created Series: {series_id}")
                else:
                    print(f"✓ Found Series: {series_id}")
                
                series_registry[(symbol, tf)] = series

                # Check/Create Bars using consistent timeline
                # We'll generate bars for the last 5 days to keep it fast but relevant
                # Only if they don't exist
                bar_count = db.query(RunSeriesBar).filter_by(series_id=series_id).count()
                
                if bar_count < 100:
                    print(f"  generating bars for {series_id}...")
                    
                    # Logic: Generate 1 bar per interval? No, just dummy 'N' bars covering the range evenly
                    # For visualization, let's just do 500 bars ending at now
                    
                    num_bars = 500
                    base_price = 60000 if "BTC" in symbol else (3000 if "ETH" in symbol else 150)
                    
                    # Simple Walk
                    bars = []
                    current_price = base_price
                    
                    # Determine interval delta (approximate for dummy data)
                    delta = timedelta(minutes=1) 
                    if tf == "5m": delta = timedelta(minutes=5)
                    if tf == "1h": delta = timedelta(hours=1)
                    
                    start_t = now_utc - (delta * num_bars)
                    
                    for i in range(num_bars):
                        t = start_t + (delta * i)
                        
                        change = random.uniform(-0.005, 0.005) # 0.5% move
                        current_price *= (1 + change)
                        
                        vol = random.uniform(1, 10)
                        
                        b = RunSeriesBar(
                            series_id=series_id,
                            ts_utc=t,
                            open=current_price,
                            high=current_price * 1.002,
                            low=current_price * 0.998,
                            close=current_price, # simplified
                            volume=vol,
                            volumetric_json={"buy": vol*0.6, "sell": vol*0.4}
                        )
                        bars.append(b)
                    
                    db.add_all(bars)
        
        db.commit()


        # --- 3. Create Instances & Runs (Linked to Data) ---
        print("Creating Instances, Runs & Trades...")
        
        # We'll create runs that align with the generated data
        # Let's say runs happened in the last 2 days
        run_start_utc = now_utc - timedelta(days=2)
        
        for s_idx, strategy in enumerate(final_strategies):
            # Create 1 instance per symbol for diversity
            target_symbol = symbols[s_idx % len(symbols)] # Rotate symbols
            target_tf = "1m" # Default to 1m for granularity
            
            # --- Instance ---
            inst = StrategyInstance(
                instance_id=str(uuid.uuid4()),
                strategy_id=strategy.strategy_id,
                instance_name=f"Live - {strategy.name} on {target_symbol}",
                parameters_json={"risk": 1.0},
                symbols_json=[target_symbol], # Required List
                timeframe=target_tf,
                venue="Binance",
                account_id="ACC_MAIN_01"
            )
            db.add(inst)
            
            # --- Run ---
            run_id = str(uuid.uuid4())
            run = StrategyRun(
                run_id=run_id,
                instance_id=inst.instance_id,
                run_type=RunType.BACKTEST,
                start_utc=run_start_utc,
                end_utc=now_utc,
                status=RunStatus.COMPLETED,
                initial_balance=10000.0,
                base_currency="USDT"
            )
            db.add(run)
            
            # --- Link Run to Series (CRITICAL STEP) ---
            series_ref = series_registry.get((target_symbol, target_tf))
            
            # Determine Time Range for Trades
            trade_start = run_start_utc
            trade_end = now_utc
            
            if series_ref:
                link = RunSeriesRunLink(
                    run_id=run_id,
                    series_id=series_ref.series_id
                )
                db.add(link)
                
                # Query actual bar range to ensure trades are valid
                min_max = db.query(func.min(RunSeriesBar.ts_utc), func.max(RunSeriesBar.ts_utc))\
                    .filter(RunSeriesBar.series_id == series_ref.series_id).first()
                if min_max and min_max[0]:
                    trade_start, trade_end = min_max
                    
                print(f"  -> Linked Run {run_id[:8]} to Series {series_ref.series_id} [{trade_start} - {trade_end}]")
            
            # --- Generate Trades within Run Window ---
            # Generate 10-20 trades
            num_trades = random.randint(10, 20)
            balance = 10000.0
            
            # Calculate average step to fit trades in the window
            total_duration = (trade_end - trade_start).total_seconds()
            if total_duration < 300: total_duration = 3600 # Safety for tiny ranges
            avg_step = total_duration / (num_trades + 2)
            
            current_trade_time = trade_start
            
            for t_i in range(num_trades):
                # Move forward proportional to range
                step = avg_step * random.uniform(0.5, 1.5)
                current_trade_time += timedelta(seconds=step)
                
                if current_trade_time >= trade_end: break
                
                side = random.choice([Side.BUY, Side.SELL])
                qty = 0.5
                
                # Price approximation (random walk logic implies we don't strictly query the DB here for speed, 
                # but valid 'clean' seed would query the bar at that time. 
                # For now, approximate based on base price of symbol)
                # Ideally: fetch price from bar? 
                # Let's just create random efficient trades
                base_p = 60000 if "BTC" in target_symbol else (3000 if "ETH" in target_symbol else 150)
                
                entry_p = base_p * random.uniform(0.9, 1.1)
                exit_p = entry_p * (1.02 if random.random() > 0.4 else 0.98) # 60% win rate
                
                pnl = (exit_p - entry_p) * qty if side == Side.BUY else (entry_p - exit_p) * qty
                balance += pnl
                
                # Trade
                trade_id = str(uuid.uuid4())
                trade = Trade(
                    trade_id=trade_id,
                    run_id=run_id,
                    symbol=target_symbol,
                    side=side,
                    entry_time=current_trade_time,
                    exit_time=current_trade_time + timedelta(minutes=15),
                    entry_price=entry_p,
                    exit_price=exit_p,
                    quantity=qty,
                    pnl_net=pnl,
                    pnl_gross=pnl,
                    commission=0.5
                )
                db.add(trade)
                
                # Executions (Entry/Exit)
                # Entry
                db.add(Execution(
                    execution_id=str(uuid.uuid4()),
                    run_id=run_id,
                    order_id=str(uuid.uuid4()), # Dummy order IDs
                    exec_utc=current_trade_time,
                    price=entry_p,
                    quantity=qty,
                    position_impact=PositionImpactType.OPEN
                ))
                 # Exit
                db.add(Execution(
                    execution_id=str(uuid.uuid4()),
                    run_id=run_id,
                    order_id=str(uuid.uuid4()),
                    exec_utc=current_trade_time + timedelta(minutes=15),
                    price=exit_p,
                    quantity=qty,
                    position_impact=PositionImpactType.CLOSE
                ))

        db.commit()


        # --- 4. ML Data (Optional but good for completeness) ---
        print("Creating ML Metadata...")
        # Keeping it minimal as focus is on Trades/Regime
        
        # ... (ML seeding logic can be kept minimal or copied if needed, 
        # but for robustness let's just create one session)
        
        # Reward Function
        rf = MlRewardFunction(
             function_id=str(uuid.uuid4()),
             name="Simple PnL",
             code="return env.pnl",
             description="Simple PnL Reward"
        )
        db.add(rf)
        
        # Architecture
        arch = MlModelArchitecture(
            model_id=str(uuid.uuid4()),
            name="DQN Simple",
            layers_json=[]
        )
        db.add(arch)
        
        # Process
        proc = MlTrainingProcess(
            process_id=str(uuid.uuid4()),
            name="Default Process"
        )
        db.add(proc)
        
        db.commit()
    
    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()
        print("✅ Seed Complete.")

if __name__ == "__main__":
    create_dummy_data()
