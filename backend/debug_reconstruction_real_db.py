from src.database.connection import get_db
from src.database.models import Order, Execution, StrategyRun
from src.quantlab.metrics import MetricsEngine

def debug_real_data():
    db = next(get_db())
    print(" Fetching latest run...")
    
    # Get latest run with executions
    run = db.query(StrategyRun).order_by(StrategyRun.start_utc.desc()).first()
    
    if not run:
        print("No runs found.")
        return

    print(f"Analyzing Run: {run.run_id} (Status: {run.status})")
    
    orders = db.query(Order).filter(Order.run_id == run.run_id).all()
    executions = db.query(Execution).filter(Execution.run_id == run.run_id).all()
    
    print(f"Orders: {len(orders)}")
    print(f"Executions: {len(executions)}")
    
    if not executions:
        print("No executions for this run.")
        return

    print("Attempting reconstruction...")
    trades = MetricsEngine.reconstruct_trades(executions, orders)
    
    print(f"Reconstructed Trades: {len(trades)}")
    
    if not trades:
        print("DEBUGGING: Why no trades?")
        # Print first few orders/execs
        print("Sample Orders:")
        for o in orders[:5]:
            print(f"  {o.order_id} {o.side} {o.symbol} Qty:{o.quantity}")
            
        print("Sample Executions:")
        for e in executions[:5]:
            print(f"  {e.execution_id} Ord:{e.order_id} Qty:{e.quantity} Price:{e.price}")
            
    else:
        print("First 5 trades:")
        for t in trades[:5]:
            print(t)
            
        calc_metrics = MetricsEngine.calculate_trade_metrics(trades)
        print("Metrics:", calc_metrics)

if __name__ == "__main__":
    debug_real_data()
