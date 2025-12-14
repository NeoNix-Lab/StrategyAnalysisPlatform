from src.database.connection import SessionLocal, init_db
from src.core.trade_service import TradeService
from src.database.models import Trade

def test_persistence():
    # Ensure tables exist (including new Trade)
    init_db()
    
    db = SessionLocal()
    try:
        # Check if we can query Trades (table exists)
        count = db.query(Trade).count()
        print(f"Current Trades in DB: {count}")
        
        # Try a rebuild on a known run (if any)
        # Find a run with executions
        from src.database.models import Execution, StrategyRun
        run = db.query(StrategyRun).join(StrategyRun.executions).first()
        
        if run:
            print(f"Testing rebuild for run: {run.run_id}")
            service = TradeService(db)
            rebuilt_count = service.rebuild_trades_for_run(run.run_id)
            print(f"Rebuilt {rebuilt_count} trades.")
            
            # Verify persistence
            new_count = db.query(Trade).filter(Trade.run_id == run.run_id).count()
            print(f"Trades in DB for this run: {new_count}")
            assert new_count == rebuilt_count
        else:
            print("No runs with executions found to test.")
            
    except Exception as e:
        print(f"Test Failed: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    test_persistence()
