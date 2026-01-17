import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Strategy, StrategyInstance, StrategyRun, Order, Execution

def resolve_db_path() -> str:
    env_path = os.getenv("TRADING_DB_PATH")
    if env_path:
        return env_path
    project_root = Path(__file__).resolve().parents[3]
    var_db = project_root / "var" / "trading_data.db"
    if var_db.exists():
        return str(var_db)
    return str(project_root / "trading_data.db")

# Database connection
SQLALCHEMY_DATABASE_URL = f"sqlite:///{resolve_db_path()}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("--- Database Relationship Verification ---\n")

strategies = db.query(Strategy).all()
print(f"Total Strategies: {len(strategies)}")

for strat in strategies:
    print(f"\nStrategy: {strat.name} (ID: {strat.strategy_id})")
    print(f"  Instances: {len(strat.instances)}")
    
    for inst in strat.instances:
        print(f"    Instance: {inst.instance_name} (ID: {inst.instance_id})")
        print(f"      Parameters: {inst.parameters_json}")
        print(f"      Runs: {len(inst.runs)}")
        
        for run in inst.runs:
            print(f"        Run: {run.run_id} (Start: {run.start_utc})")
            print(f"          Orders: {len(run.orders)}")
            print(f"          Executions: {len(run.executions)}")
            
            # optional: verify executions link to orders that belong to the run
            if run.executions and run.orders:
                order_ids = set(o.order_id for o in run.orders)
                for exc in run.executions:
                    if exc.order_id not in order_ids:
                        print(f"          [WARNING] Execution {exc.execution_id} references unknown Order {exc.order_id}")
                    else:
                         pass # Link valid


print("\n--- Verification Complete ---")
db.close()

# Also write to file for Agent to read easily
with open("verification_report_utf8.txt", "w", encoding="utf-8") as f:
    f.write("--- Database Relationship Verification ---\n")
    f.write(f"Total Strategies: {len(strategies)}\n")
    for strat in strategies:
        f.write(f"\nStrategy: {strat.name} (ID: {strat.strategy_id})\n")
        f.write(f"  Instances: {len(strat.instances)}\n")
        for inst in strat.instances:
            f.write(f"    Instance: {inst.instance_name} (ID: {inst.instance_id})\n")
            f.write(f"      Parameters: {inst.parameters_json}\n")
            f.write(f"      Runs: {len(inst.runs)}\n")
            for run in inst.runs:
                f.write(f"        Run: {run.run_id} (Start: {run.start_utc})\n")
                f.write(f"          Orders: {len(run.orders)}\n")
                f.write(f"          Executions: {len(run.executions)}\n")
                if run.executions and run.orders:
                    order_ids = set(o.order_id for o in run.orders)
                    for exc in run.executions:
                        if exc.order_id not in order_ids:
                             f.write(f"          [WARNING] Execution {exc.execution_id} references unknown Order {exc.order_id}\n")

