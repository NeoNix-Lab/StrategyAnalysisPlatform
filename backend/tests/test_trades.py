import pytest
import uuid
from datetime import datetime, timedelta
from src.core.trade_service import TradeService
from src.database.models import Trade, Execution, Order, StrategyRun, StrategyInstance, Side, OrderType, RunType, OrderStatus

def test_rebuild_trades(db_session):
    # 1. Setup Test Data
    run_id = str(uuid.uuid4())
    instance_id = str(uuid.uuid4())
    strategy_id = "TEST_STRA_ID"
    
    # Create Instance
    instance = StrategyInstance(
        instance_id=instance_id,
        strategy_id=strategy_id,
        parameters_json={}
    )
    db_session.add(instance)
    
    # Create Run
    run = StrategyRun(
        run_id=run_id,
        instance_id=instance_id,
        run_type=RunType.BACKTEST
    )
    db_session.add(run)
    db_session.commit()
    
    # Create Orders & Executions for a simple Long Trade
    # Buy Order
    buy_order_id = "ORD_1"
    buy_order = Order(
        run_id=run_id,
        order_id=buy_order_id,
        symbol="EURUSD",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        quantity=1.0,
        status=OrderStatus.FILLED
    )
    db_session.add(buy_order)
    
    # Buy Execution
    buy_exec = Execution(
        execution_id="EXEC_1",
        run_id=run_id,
        order_id=buy_order_id,
        exec_utc=datetime.utcnow() - timedelta(minutes=10),
        price=1.1000,
        quantity=1.0,
        fee=0.0
    )
    db_session.add(buy_exec)
    
    # Sell Order
    sell_order_id = "ORD_2"
    sell_order = Order(
        run_id=run_id,
        order_id=sell_order_id,
        symbol="EURUSD",
        side=Side.SELL,
        order_type=OrderType.MARKET,
        quantity=1.0,
        status=OrderStatus.FILLED
    )
    db_session.add(sell_order)
    
    # Sell Execution (Close)
    sell_exec = Execution(
        execution_id="EXEC_2",
        run_id=run_id,
        order_id=sell_order_id,
        exec_utc=datetime.utcnow(),
        price=1.1050, # 50 pips profit
        quantity=1.0,
        fee=0.0
    )
    db_session.add(sell_exec)
    
    db_session.commit()
    
    # 2. Run Test
    service = TradeService(db_session)
    count = service.rebuild_trades_for_run(run_id)
    
    # 3. Verify
    assert count == 1
    
    trades = db_session.query(Trade).filter(Trade.run_id == run_id).all()
    assert len(trades) == 1
    t = trades[0]
    
    assert t.symbol == "EURUSD"
    assert t.side == Side.BUY
    assert t.entry_price == 1.1000
    assert t.exit_price == 1.1050
    assert t.pnl_gross == (1.1050 - 1.1000) * 1.0 # approx 0.005
    assert t.quantity == 1.0
