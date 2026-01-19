import sys
import os
from sqlalchemy import create_engine
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

TARGET_EMAIL = "rittoone@gmail.com"
user = session.query(User).filter_by(email=TARGET_EMAIL).first()

if not user:
    print(f"User {TARGET_EMAIL} not found!")
    sys.exit(1)

print(f"Migrating ORPHANED objects to user: {user.email} (ID: {user.user_id})")

def migrate_table(Model, name):
    count = session.query(Model).filter(Model.user_id == None).update({Model.user_id: user.user_id}, synchronize_session=False)
    print(f"Updated {count} {name}.")

migrate_table(Strategy, "Strategies")
migrate_table(StrategyInstance, "Strategy Instances")
# Dataset already checked/migrated but good to include
migrate_table(Dataset, "Datasets")
migrate_table(MlRewardFunction, "ML Reward Functions")
migrate_table(MlModelArchitecture, "ML Architectures")
migrate_table(MlTrainingProcess, "ML Processes")
migrate_table(MlTrainingSession, "ML Sessions")

session.commit()
print("Migration complete.")
