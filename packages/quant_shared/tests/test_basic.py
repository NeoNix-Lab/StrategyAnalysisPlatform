import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from quant_shared.models.models import Base, StrategyRun
from quant_shared.schemas.schemas import StrategyRunCreate, StartRunRequest
from datetime import datetime

def test_models_creation():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    
    Session = sessionmaker(bind=engine)
    session = Session()
    
    run = StrategyRun(run_id="test_run", instance_id="inst_1", run_type="BACKTEST")
    session.add(run)
    session.commit()
    
    assert session.query(StrategyRun).count() == 1
    session.close()

def test_schemas_instantiation():
    req = StartRunRequest(strategy_id="test_strat", parameters={"a": 1})
    assert req.strategy_id == "test_strat"
    
    run_create = StrategyRunCreate(
        run_id="run_1", 
        instance_id="inst_1", 
        run_type="BACKTEST", 
        start_utc=datetime.utcnow()
    )
    assert run_create.run_id == "run_1"
