from src.database.connection import engine
from sqlalchemy import inspect
from src.database.models import Trade, Bar, Order, Execution
from sqlalchemy.orm import Session

# Check tables
insp = inspect(engine)
print("Tabelle nel database:", insp.get_table_names())

# Count records
with Session(engine) as db:
    trade_count = db.query(Trade).count()
    bar_count = db.query(Bar).count()
    order_count = db.query(Order).count()
    exec_count = db.query(Execution).count()
    
    print(f"\nConteggio record:")
    print(f"  Trades: {trade_count}")
    print(f"  Bars: {bar_count}")
    print(f"  Orders: {order_count}")
    print(f"  Executions: {exec_count}")
    
    if trade_count > 0:
        print("\nPrimi 3 trade:")
        trades = db.query(Trade).limit(3).all()
        for t in trades:
            print(f"  - {t.trade_id}: {t.symbol} {t.side} PnL={t.pnl_net}")
