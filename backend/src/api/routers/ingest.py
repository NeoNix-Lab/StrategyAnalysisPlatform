from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import logging
from datetime import datetime
import uuid
import hashlib

from src.database.connection import get_db
from src.database.models import (
    Strategy, StrategyInstance, StrategyRun, 
    Order, Execution, RunSeries, Bar,
    MarketSeries, MarketBar, RunSubscription,
    Side, OrderType, OrderStatus, PositionImpactType, RunType, RunStatus
)
from src.api.schemas import (
    StrategyCreate, StrategyInstanceCreate, StrategyRunCreate, StrategyRunUpdate,
    OrderCreate, OrderUpdate, ExecutionCreate, BarCreate
)
from src.core.trade_service import TradeService

router = APIRouter()
logger = logging.getLogger(__name__)

# --- Helper Functions ---

def upsert_strategy(db: Session, data: StrategyCreate):
    strat = db.query(Strategy).filter(Strategy.strategy_id == data.strategy_id).first()
    if not strat:
        strat = Strategy(
            strategy_id=data.strategy_id,
            name=data.name,
            version=data.version,
            vendor=data.vendor,
            source_ref=data.source_ref,
            notes=data.notes
        )
        db.add(strat)
    else:
        # Update updatable fields if they are not None ?
        # Strategy definition is mostly static, but version might change.
        if data.version:
            strat.version = data.version
        if data.name:
            strat.name = data.name
    db.commit()
    db.refresh(strat)
    return strat

def upsert_instance(db: Session, data: StrategyInstanceCreate):
    inst = db.query(StrategyInstance).filter(StrategyInstance.instance_id == data.instance_id).first()
    if not inst:
        inst = StrategyInstance(
            instance_id=data.instance_id,
            strategy_id=data.strategy_id,
            instance_name=data.instance_name,
            parameters_json=data.parameters_json,
            symbol=data.symbol,
            symbols_json=data.symbols_json,
            timeframe=data.timeframe,
            account_id=data.account_id,
            venue=data.venue
        )
        db.add(inst)
    else:
        inst.parameters_json = data.parameters_json
        if data.instance_name: inst.instance_name = data.instance_name
        # ... update other fields
    db.commit()
    db.refresh(inst)
    return inst

# --- Endpoints ---

@router.post("/event/strategy_create")
def on_strategy_create(data: StrategyCreate, db: Session = Depends(get_db)):
    try:
        upsert_strategy(db, data)
        return {"status": "ok", "id": data.strategy_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating strategy: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/event/instance_create")
def on_instance_create(data: StrategyInstanceCreate, db: Session = Depends(get_db)):
    try:
        # Ensure strategy exists first? 
        # Ideally client sends strategy_create. If not, this might fail with FK error.
        upsert_instance(db, data)
        return {"status": "ok", "id": data.instance_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating instance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/event/run_start")
def on_run_start(data: StrategyRunCreate, db: Session = Depends(get_db)):
    try:
        run = db.query(StrategyRun).filter(StrategyRun.run_id == data.run_id).first()
        if not run:
            run = StrategyRun(
                run_id=data.run_id,
                instance_id=data.instance_id,
                run_type=RunType(data.run_type), # Convert string to Enum
                start_utc=data.start_utc,
                status=RunStatus.RUNNING,
                engine_version=data.engine_version,
                data_source=data.data_source,
                initial_balance=data.initial_balance,
                base_currency=data.base_currency,
                metrics_json=data.metrics_json
            )
            db.add(run)
        else:
            # Maybe restart? Update?
            pass
        db.commit()
        return {"status": "ok", "id": data.run_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error starting run: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/event/order")
async def on_order(data: OrderCreate, db: Session = Depends(get_db)):
    logger.info(f"Received Order Event: {data.order_id} (Status: {data.status})")
    try:
        await upsert_order_logic(db, data)
        db.commit()
        return {"status": "ok", "id": data.order_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/orders")
async def on_orders_batch(data: list[OrderCreate], db: Session = Depends(get_db)):
    try:
        for item in data:
            await upsert_order_logic(db, item)
        db.commit()
        return {"status": "ok", "count": len(data)}
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing order batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def upsert_order_logic(db: Session, data: OrderCreate):
    existing = db.query(Order).filter(Order.run_id == data.run_id, Order.order_id == data.order_id).first()
    if existing:
        existing.status = OrderStatus(data.status)
        existing.quantity = data.quantity 
        existing.price = data.price
        existing.update_utc = data.submit_utc
        if data.position_impact:
            existing.position_impact = PositionImpactType(data.position_impact)
    else:
        new_order = Order(
            run_id=data.run_id,
            strategy_id=data.strategy_id,
            order_id=data.order_id,
            parent_order_id=data.parent_order_id,
            symbol=data.symbol,
            account_id=data.account_id,
            side=Side(data.side),
            order_type=OrderType(data.order_type),
            time_in_force=data.time_in_force,
            quantity=data.quantity,
            price=data.price,
            stop_price=data.stop_price,
            status=OrderStatus(data.status),
            submit_utc=data.submit_utc,
            client_tag=data.client_tag,
            position_impact=PositionImpactType(data.position_impact) if data.position_impact else PositionImpactType.UNKNOWN,
            extra_json=data.extra_json
        )
        db.add(new_order)
        db.flush() # Ensure visible for next iter in batch

@router.post("/event/execution")
async def on_execution(data: ExecutionCreate, db: Session = Depends(get_db)):
    logger.info(f"Received Execution Event: {data.execution_id} for Order {data.order_id}")
    try:
        await upsert_execution_logic(db, data)
        db.commit()
        return {"status": "ok", "id": data.execution_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/executions")
async def on_executions_batch(data: list[ExecutionCreate], background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    try:
        run_ids = set()
        for item in data:
            await upsert_execution_logic(db, item)
            run_ids.add(item.run_id)
        db.commit()
        
        # Trigger Trade Reconstruction for affected runs
        trade_service = TradeService(db)
        for rid in run_ids:
            # We can't pass db session to background task safely if it closes. 
            # Ideally background task opens its own session.
            # For now, let's run it synchronously or structure a proper background worker.
            # Given SQLite/FastAPI simplicity, running it here (post-commit) or via helper that opens new session is best.
            # Let's define a helper for the background task.
            background_tasks.add_task(rebuild_trades_task, rid)
            
        return {"status": "ok", "count": len(data)}
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing execution batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def rebuild_trades_task(run_id: str):
    # Helper to open a fresh session for the background task
    db_gen = get_db()
    db = next(db_gen)
    try:
        service = TradeService(db)
        count = service.rebuild_trades_for_run(run_id)
        logger.info(f"Reconstructed {count} trades for run {run_id}")
    except Exception as e:
        logger.error(f"Error rebuilding trades for {run_id}: {e}")
    finally:
        db.close()

async def upsert_execution_logic(db: Session, data: ExecutionCreate):
    existing = db.query(Execution).filter(Execution.run_id == data.run_id, Execution.execution_id == data.execution_id).first()
    if existing:
        existing.order_id = data.order_id
        existing.exec_utc = data.exec_utc
        existing.price = data.price
        existing.quantity = data.quantity
        existing.fee = data.fee
        existing.fee_currency = data.fee_currency
        existing.liquidity = data.liquidity
        if data.position_impact:
            existing.position_impact = PositionImpactType(data.position_impact)
        existing.extra_json = data.extra_json
    else:
        exec_obj = Execution(
            run_id=data.run_id,
            execution_id=data.execution_id,
            order_id=data.order_id,
            exec_utc=data.exec_utc,
            price=data.price,
            quantity=data.quantity,
            fee=data.fee,
            fee_currency=data.fee_currency,
            liquidity=data.liquidity,
            position_impact=PositionImpactType(data.position_impact) if data.position_impact else PositionImpactType.UNKNOWN,
            extra_json=data.extra_json

        )
        db.add(exec_obj)
        db.flush() # Ensure visible for next iter in batch

@router.post("/event/bar")
async def on_bar(data: BarCreate, db: Session = Depends(get_db)):
    try:
        await upsert_bar_logic(db, data)
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing bar: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch/bars")
async def on_bars_batch(data: list[BarCreate], db: Session = Depends(get_db)):
    try:
        for item in data:
            await upsert_bar_logic(db, item)
        db.commit()
        return {"status": "ok", "count": len(data)}
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing bar batch: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def upsert_bar_logic(db: Session, data: BarCreate):
    # "Unified Market Data Layer" Logic
    
    # 1. Calculate MarketSeries ID (Hash)
    series_key = f"{data.symbol}_{data.timeframe}_{data.venue}_{data.provider}"
    series_id = hashlib.md5(series_key.encode()).hexdigest()
    
    # 2. Ensure MarketSeries Exists
    market_series = db.query(MarketSeries).filter(MarketSeries.series_id == series_id).first()
    if not market_series:
        market_series = MarketSeries(
            series_id=series_id,
            symbol=data.symbol,
            timeframe=data.timeframe,
            venue=data.venue,
            provider=data.provider,
            created_utc=datetime.utcnow()
        )
        db.add(market_series)
        db.flush() # Flush to make ID available, but don't commit yet if in batch

    # 3. Ensure Run Subscription (Run -> MarketSeries)
    sub = db.query(RunSubscription).filter(
        RunSubscription.run_id == data.run_id,
        RunSubscription.series_id == series_id
    ).first()
    
    if not sub:
        sub = RunSubscription(run_id=data.run_id, series_id=series_id)
        db.add(sub)
        db.flush() # Ensure visible for next iter in batch
    
    # 4. Upsert Bar in MarketBar
    existing = db.query(MarketBar).filter(
        MarketBar.series_id == series_id,
        MarketBar.ts_utc == data.ts_utc
    ).first()
    
    if existing:
        # Update
        existing.open = data.open
        existing.high = data.high
        existing.low = data.low
        existing.close = data.close
        existing.volume = data.volume
        existing.volumetric_json = data.volumetric_json
    else:
        new_bar = MarketBar(
            series_id=series_id,
            ts_utc=data.ts_utc,
            open=data.open,
            high=data.high,
            low=data.low,
            close=data.close,
            volume=data.volume,
            volumetric_json=data.volumetric_json

        )
        db.add(new_bar)
        db.flush() # Ensure visible for next iter in batch
