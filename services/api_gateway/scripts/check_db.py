from src.database.connection import engine
from sqlalchemy import inspect
from src.database.models import Bar, Order, Execution, Strategy, StrategyInstance, StrategyRun
from sqlalchemy.orm import Session
import sys

# Redirect stdout to file
with open("db_status_utf8.txt", "w", encoding="utf-8") as f:
    # Check tables
    insp = inspect(engine)
    f.write(f"Tabelle nel database: {insp.get_table_names()}\n")

    # Count records
    with Session(engine) as db:
        strat_count = db.query(Strategy).count()
        run_count = db.query(StrategyRun).count()
        bar_count = db.query(Bar).count()
        order_count = db.query(Order).count()
        exec_count = db.query(Execution).count()
        
        f.write(f"\nConteggio record:\n")
        f.write(f"  Strategies: {strat_count}\n")
        f.write(f"  Runs: {run_count}\n")
        f.write(f"  Bars: {bar_count}\n")
        f.write(f"  Orders: {order_count}\n")
        f.write(f"  Executions: {exec_count}\n")

        if run_count > 0:
            f.write("\nUltimi Run:\n")
            runs = db.query(StrategyRun).order_by(StrategyRun.created_utc.desc()).limit(3).all()
            for r in runs:
                f.write(f"  - {r.run_id} ({r.status}) started at {r.start_utc}\n")
