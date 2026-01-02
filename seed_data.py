
import random
from datetime import datetime, timedelta
import uuid
import json

from sqlalchemy.orm import Session
from quant_shared.models.connection import get_db, init_db, engine
from quant_shared.models.models import (
    Strategy, StrategyInstance, StrategyRun, Trade, Execution, Order,
    Dataset, MlRewardFunction, MlModelArchitecture, MlTrainingProcess, 
    MlTrainingSession, MlIteration,
    RunType, RunStatus, Side, OrderType, OrderStatus, PositionImpactType,
    Base
)

def create_dummy_data():
    print("🚀 Initializing DB...")
    init_db()
    
    db = next(get_db())
    
    try:
        # 1. Create Strategies
        print("Creating Strategies...")
        strategies = [
            Strategy(
                strategy_id=str(uuid.uuid4()),
                name="TrendFollower Alpha",
                version="1.0.2",
                vendor="QuantLab",
                notes="Standard moving average crossover"
            ),
            Strategy(
                strategy_id=str(uuid.uuid4()),
                name="MeanReversion X",
                version="2.1.0",
                vendor="External",
                notes="Bollinger bands strategy"
            ),
             Strategy(
                strategy_id=str(uuid.uuid4()),
                name="DeepRL Trader",
                version="0.5.0-beta",
                vendor="AI Lab",
                notes="PPO agent trained on BTCUSDT"
            )
        ]
        
        for s in strategies:
            exists = db.query(Strategy).filter_by(name=s.name).first()
            if not exists:
                db.add(s)
            else:
                strategies[strategies.index(s)] = exists # Use existing
        
        db.commit()
        
        # 2. Create Instances
        print("Creating Instances...")
        instances = []
        symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
        timeframes = ["1m", "5m", "1h", "4h"]
        
        for s in strategies:
            for i in range(2): # 2 instances per strategy
                inst = StrategyInstance(
                    instance_id=str(uuid.uuid4()),
                    strategy_id=s.strategy_id,
                    instance_name=f"{s.name} - {symbols[i]} {timeframes[i]}",
                    parameters_json={"period": 14, "std_dev": 2.0},
                    symbol=symbols[i],
                    timeframe=timeframes[i],
                    venue="Binance",
                    account_id="ACC_BIN_001"
                )
                db.add(inst)
                instances.append(inst)
        
        db.commit()

        # 3. Create Runs & Trades
        print("Creating Runs and Trades...")
        
        start_date = datetime.utcnow() - timedelta(days=30)
        
        for inst in instances:
            # Create 1 main run per instance
            run = StrategyRun(
                run_id=str(uuid.uuid4()),
                instance_id=inst.instance_id,
                run_type=RunType.BACKTEST,
                start_utc=start_date,
                end_utc=datetime.utcnow(),
                status=RunStatus.COMPLETED,
                initial_balance=10000.0,
                base_currency="USDT"
            )
            db.add(run)
            db.commit() # Commit to get run ID valid
            
            # Generate random trades
            balance = 10000.0
            equity = []
            
            current_time = start_date
            for _ in range(random.randint(20, 50)): # 20-50 trades per run
                current_time += timedelta(hours=random.randint(1, 12))
                if current_time > datetime.utcnow(): break
                
                side = random.choice([Side.BUY, Side.SELL])
                entry_price = random.uniform(20000, 60000) if "BTC" in inst.symbol else random.uniform(1000, 3000)
                exit_price = entry_price * (1 + random.uniform(-0.02, 0.03)) # -2% to +3%
                
                qty = 0.1 if "BTC" in inst.symbol else 1.0
                
                pnl = (exit_price - entry_price) * qty if side == Side.BUY else (entry_price - exit_price) * qty
                balance += pnl
                
                trade = Trade(
                    trade_id=str(uuid.uuid4()),
                    run_id=run.run_id,
                    symbol=inst.symbol,
                    side=side,
                    entry_time=current_time,
                    exit_time=current_time + timedelta(minutes=random.randint(5, 120)),
                    entry_price=entry_price,
                    exit_price=exit_price,
                    quantity=qty,
                    pnl_net=pnl,
                    pnl_gross=pnl,
                    commission=pnl * 0.01
                )
                db.add(trade)
                
                # Create fake execution for entry
                exec_entry = Execution(
                    run_id=run.run_id,
                    execution_id=str(uuid.uuid4()),
                    order_id=str(uuid.uuid4()),
                    exec_utc=current_time,
                    price=entry_price,
                    quantity=qty,
                    position_impact=PositionImpactType.OPEN
                )
                db.add(exec_entry)

        # 4. Create ML Studio Data
        print("Creating ML Studio Data...")
        
        # --- Datasets ---
        datasets_to_seed = [
            Dataset(
                dataset_id=str(uuid.uuid4()),
                name="BTC 1m High Volatility",
                description="BTCUSDT 1m bars from 2023-01-01 with RSI > 70",
                sources_json=[{"run_id": "none", "symbol": "BTCUSDT", "timeframe": "1m"}],
                feature_config_json=["open", "high", "low", "close", "volume"]
            ),
            Dataset(
                dataset_id=str(uuid.uuid4()),
                name="ETH 5m Trend",
                description="ETHUSDT 5m bars for trend following training",
                sources_json=[{"run_id": "none", "symbol": "ETHUSDT", "timeframe": "5m"}],
                feature_config_json=["open", "high", "low", "close", "volume", "rsi_14", "ema_50"]
            )
        ]
        for ds in datasets_to_seed:
            db.add(ds)
        
        # --- Reward Functions ---
        reward_fns = [
            MlRewardFunction(
                function_id=str(uuid.uuid4()),
                name="Simple PnL",
                description="Directly rewards unrealized profit/loss",
                code="def calculate_reward(env, action):\n    # Simply return the current unrealized PnL\n    return env.unrealized_pnl",
                metadata_json={"action_labels": ["HOLD", "BUY", "SELL"], "status_labels": ["FLAT", "LONG", "SHORT"]}
            ),
            MlRewardFunction(
                function_id=str(uuid.uuid4()),
                name="Sharpe Reward (Approx)",
                description="Rewards returns adjusted by volatility",
                code="def calculate_reward(env, action):\n    # Mocked Sharpe: reward / (volatility + epsilon)\n    # In a real environment, you'd track historical rewards\n    pnl = env.unrealized_pnl\n    reward = pnl\n    if abs(pnl) < 1.0:\n        reward = 0\n    return reward",
                metadata_json={"action_labels": ["HOLD", "BUY", "SELL"], "status_labels": ["FLAT", "LONG", "SHORT"]}
            ),
            MlRewardFunction(
                function_id=str(uuid.uuid4()),
                name="Directional Accuracy",
                description="Rewards being in the correct position relative to next move",
                code="def calculate_reward(env, action):\n    # This is a placeholder for complex directional logic\n    # Reward 1.0 if position matches trend, else -1.0\n    reward = 0\n    if env.position == env.status.LONG and env.data['close'].iloc[-1] > env.entry_price:\n        reward = 1.0\n    elif env.position == env.status.SHORT and env.data['close'].iloc[-1] < env.entry_price:\n        reward = 1.0\n    else:\n        reward = -0.1\n    return reward",
                metadata_json={"action_labels": ["HOLD", "BUY", "SELL"], "status_labels": ["FLAT", "LONG", "SHORT"]}
            )
        ]
        for rf in reward_fns:
            db.add(rf)
        
        # --- Model Architectures ---
        architectures = [
            MlModelArchitecture(
                model_id=str(uuid.uuid4()),
                name="DQN Small (2-Layer)",
                description="Lightweight 2-layer Dense network",
                layers_json=[
                    {"type": "Dense", "units": 32, "activation": "relu"},
                    {"type": "Dense", "units": 16, "activation": "relu"},
                    {"type": "Dense", "units": 3, "activation": "linear"}
                ]
            ),
            MlModelArchitecture(
                model_id=str(uuid.uuid4()),
                name="DQN Standard (3-Layer)",
                description="Balanced 3-layer Dense network",
                layers_json=[
                    {"type": "Dense", "units": 64, "activation": "relu"},
                    {"type": "Dense", "units": 64, "activation": "relu"},
                    {"type": "Dense", "units": 32, "activation": "relu"},
                    {"type": "Dense", "units": 3, "activation": "linear"}
                ]
            ),
            MlModelArchitecture(
                model_id=str(uuid.uuid4()),
                name="LSTM Sequence Trader",
                description="Uses LSTM for temporal feature extraction",
                layers_json=[
                    {"type": "LSTM", "units": 64, "return_sequences": True},
                    {"type": "LSTM", "units": 32, "return_sequences": False},
                    {"type": "Dense", "units": 3, "activation": "linear"}
                ]
            )
        ]
        for arch in architectures:
            db.add(arch)
        
        # --- Training Processes ---
        processes = [
            MlTrainingProcess(
                process_id=str(uuid.uuid4()),
                name="Fast Test Cycle",
                gamma=0.9,
                learning_rate=0.001,
                epochs=5,
                batch_size=32,
                epsilon_start=1.0,
                epsilon_end=0.1,
                epsilon_decay=0.8,
                description="Very fast training for UI and flow testing"
            ),
            MlTrainingProcess(
                process_id=str(uuid.uuid4()),
                name="Stable DQN Production",
                gamma=0.99,
                learning_rate=0.0001,
                epochs=100,
                batch_size=64,
                epsilon_start=1.0,
                epsilon_end=0.01,
                epsilon_decay=0.995,
                description="Balanced settings for actual model training"
            )
        ]
        for p in processes:
            db.add(p)
            
        db.commit()

        # --- Training Sessions ---
        session = MlTrainingSession(
            session_id=str(uuid.uuid4()),
            name="BTC Alpha Exploration",
            function_id=reward_fns[0].function_id,
            model_id=architectures[1].model_id,
            process_id=processes[1].process_id,
            status="ACTIVE"
        )
        db.add(session)
        db.commit()

        print("✅ Database populated (with coherent ML defaults) successfully!")

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_dummy_data()
