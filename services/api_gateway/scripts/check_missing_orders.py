from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.database.models import Order, Execution

SQLALCHEMY_DATABASE_URL = "sqlite:///trading_data.db"
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
