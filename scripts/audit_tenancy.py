import sys
import os
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath("packages/quant_shared/src"))
from quant_shared.models.models import (
    User, Strategy, StrategyInstance, Dataset, 
    MlRewardFunction, MlModelArchitecture, MlTrainingProcess, MlTrainingSession
)

DB_PATH = "trading_data.db"
if not os.path.exists(DB_PATH):
    print(f"Error: {DB_PATH} not found")
    sys.exit(1)

engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
session = Session()

# 1. Get All Users
users = session.query(User).all()
user_map = {u.user_id: u.email for u in users}

# 2. Add "Orphaned" (None) pseudouser
user_map[None] = "ORPHANED (No Owner)"

print(f"{'User Email':<40} | {'Strat':<5} | {'Inst':<5} | {'Data':<5} | {'RewFn':<5} | {'Arch':<5} | {'Proc':<5} | {'Sess':<5}")
print("-" * 100)

stats = {}
for uid in user_map.keys():
    stats[uid] = {
        "strategies": 0, "instances": 0, "datasets": 0, 
        "rewards": 0, "archs": 0, "processes": 0, "sessions": 0
    }

# Helper to aggregate counts
def count_table(Model, name):
    counts = session.query(Model.user_id, func.count(Model.user_id)).group_by(Model.user_id).all()
    # Handle NULLs explicitly if not returned by group_by (depends on SQL dialect, usually returned as None)
    # Also check for explicit filtering for None if needed, but group_by usually works.
    
    # We also need to catch the "None" group specific count query if group_by skips nulls in some engines, 
    # but SQLite usually includes None group.
    
    # Let's iterate and fill
    for (uid, count) in counts:
        if uid not in stats: stats[uid] = {"strategies": 0, "instances": 0, "datasets": 0, "rewards": 0, "archs": 0, "processes": 0, "sessions": 0} # Should cover unknown users if any
        stats[uid][name] = count

    # Also count orphans explicitly to be safe
    orphans = session.query(func.count()).filter(Model.user_id == None).scalar()
    if orphans > 0:
        if None not in stats: stats[None] = {"strategies": 0, "instances": 0, "datasets": 0, "rewards": 0, "archs": 0, "processes": 0, "sessions": 0}
        stats[None][name] = orphans

count_table(Strategy, "strategies")
count_table(StrategyInstance, "instances")
count_table(Dataset, "datasets")
count_table(MlRewardFunction, "rewards")
count_table(MlModelArchitecture, "archs")
count_table(MlTrainingProcess, "processes")
count_table(MlTrainingSession, "sessions")

for uid, email in user_map.items():
    s = stats.get(uid, {"strategies": 0, "instances": 0, "datasets": 0, "rewards": 0, "archs": 0, "processes": 0, "sessions": 0})
    print(f"{email:<40} | {s['strategies']:<5} | {s['instances']:<5} | {s['datasets']:<5} | {s['rewards']:<5} | {s['archs']:<5} | {s['processes']:<5} | {s['sessions']:<5}")

# Print aggregated orphans if present and not in loop
if None in stats:
    s = stats[None]
    if any(v > 0 for v in s.values()):
        print(f"{'ORPHANED (No Owner)':<40} | {s['strategies']:<5} | {s['instances']:<5} | {s['datasets']:<5} | {s['rewards']:<5} | {s['archs']:<5} | {s['processes']:<5} | {s['sessions']:<5}")
