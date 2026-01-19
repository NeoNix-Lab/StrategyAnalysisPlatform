import sys
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.append(os.path.abspath("packages/quant_shared/src"))
from quant_shared.models.models import Strategy, User

DB_PATH = "trading_data.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
session = Session()

# Get User
email = "rittoone@gmail.com"
user = session.query(User).filter_by(email=email).first()
if not user:
    print("User not found")
    sys.exit(1)

print(f"Target User: {user.email}")
print(f"Target ID:   {user.user_id}")
print("-" * 60)

# Get Strategies
strategies = session.query(Strategy).all()
print(f"{'Strategy Name':<30} | {'User ID':<40} | Match?")
print("-" * 80)
for s in strategies:
    match = "YES" if s.user_id == user.user_id else "NO"
    print(f"{s.name:<30} | {s.user_id:<40} | {match}")
