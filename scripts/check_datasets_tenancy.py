import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath("packages/quant_shared/src"))
from quant_shared.models.models import Dataset

DB_PATH = "trading_data.db"
if not os.path.exists(DB_PATH):
    print(f"Error: {DB_PATH} not found")
    sys.exit(1)

engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
session = Session()

datasets = session.query(Dataset).all()
print(f"Found {len(datasets)} datasets.")
for ds in datasets:
    print(f"ID: {ds.dataset_id}, Name: {ds.name}, UserID: {ds.user_id}")
