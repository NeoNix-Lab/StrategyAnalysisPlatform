import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath("packages/quant_shared/src"))
from quant_shared.models.models import Dataset, User

DB_PATH = "trading_data.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
session = Session()

# Correct User from previous check
email = "rittoone@gmail.com"
user = session.query(User).filter_by(email=email).first()

if not user:
    print("User not found!")
    sys.exit(1)

# Find datasets with no user
datasets = session.query(Dataset).filter(Dataset.user_id == None).all()
print(f"Assigning {len(datasets)} datasets to {user.email}...")

for ds in datasets:
    ds.user_id = user.user_id
    print(f"Updated {ds.name} -> {user.user_id}")

session.commit()
print("Done.")
