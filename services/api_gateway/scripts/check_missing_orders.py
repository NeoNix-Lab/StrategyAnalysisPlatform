import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Order, Execution

def resolve_db_path() -> str:
    env_path = os.getenv("TRADING_DB_PATH")
    if env_path:
        return env_path
    project_root = Path(__file__).resolve().parents[3]
    var_db = project_root / "var" / "trading_data.db"
    if var_db.exists():
        return str(var_db)
    return str(project_root / "trading_data.db")

SQLALCHEMY_DATABASE_URL = f"sqlite:///{resolve_db_path()}"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

missing_order_ids = [
    "29036a92-5cae-4314-9edf-1ad08b17737e",
    "da81d5a6-b75c-4412-b3f4-3f2affb44f5b",
    "6a84b87c-1299-45ca-b3d0-9550250a735a"
]

print("--- Checking Missing Orders ---")
for oid in missing_order_ids:
    order = db.query(Order).filter(Order.order_id == oid).first()
    if order:
        print(f"Found Order {oid}: Run={order.run_id}, Status={order.status}")
    else:
        print(f"Order {oid} NOT FOUND in database.")

print("\n--- Checking All Orders Count ---")
count = db.query(Order).count()
print(f"Total Orders in DB: {count}")

db.close()
