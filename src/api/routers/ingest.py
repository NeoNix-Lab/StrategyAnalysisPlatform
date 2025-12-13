from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
import logging
from datetime import datetime
import uuid

from src.database.connection import get_db
from src.database.models import (
    Strategy, StrategyInstance, StrategyRun, 
    Order, Execution, RunSeries, Bar,
    Side, OrderType, OrderStatus, PositionImpactType, RunType, RunStatus
)
from src.api.schemas import (
    StrategyCreate, StrategyInstanceCreate, StrategyRunCreate, StrategyRunUpdate,
    OrderCreate, OrderUpdate, ExecutionCreate, BarCreate
)

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
        # Upsert Order
        existing = db.query(Order).filter(Order.run_id == data.run_id, Order.order_id == data.order_id).first()
        if existing:
            existing.status = OrderStatus(data.status)
            existing.quantity = data.quantity 
            existing.price = data.price
            existing.update_utc = data.submit_utc # Or separate update time?
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
        db.commit()
        return {"status": "ok", "id": data.order_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing order: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/event/execution")
async def on_execution(data: ExecutionCreate, db: Session = Depends(get_db)):
    logger.info(f"Received Execution Event: {data.execution_id} for Order {data.order_id}")
    try:
        # Idempotency check
        existing = db.query(Execution).filter(Execution.run_id == data.run_id, Execution.execution_id == data.execution_id).first()
        if not existing:
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
                extra_json=data.extra_json
            )
            db.add(exec_obj)
            db.commit()
        return {"status": "ok", "id": data.execution_id}
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing execution: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/event/bar")
def on_bar(data: BarCreate, db: Session = Depends(get_db)):
    try:
        # 1. Find or Create RunSeries
        series = db.query(RunSeries).filter(
            RunSeries.run_id == data.run_id,
            RunSeries.symbol == data.symbol,
            RunSeries.timeframe == data.timeframe
        ).first()
        
        if not series:
            series_id = str(uuid.uuid4())
            series = RunSeries(
                series_id=series_id,
                run_id=data.run_id,
                symbol=data.symbol,
                timeframe=data.timeframe,
                created_utc=datetime.utcnow()
            )
            db.add(series)
            db.commit()
            db.refresh(series)
        
        # 2. Insert Bar
        existing_bar = db.query(Bar).filter(Bar.series_id == series.series_id, Bar.ts_utc == data.ts_utc).first()
        if existing_bar:
            # Update
            existing_bar.open = data.open
            existing_bar.high = data.high
            existing_bar.low = data.low
            existing_bar.close = data.close
            existing_bar.volume = data.volume
            existing_bar.volumetric_json = data.volumetric_json
        else:
            bar = Bar(
                series_id=series.series_id,
                ts_utc=data.ts_utc,
                open=data.open,
                high=data.high,
                low=data.low,
                close=data.close,
                volume=data.volume,
                volumetric_json=data.volumetric_json
            )
            db.add(bar)
        
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error processing bar: {e}")
        raise HTTPException(status_code=500, detail=str(e))
