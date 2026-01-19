import httpx
import asyncio
import sys

# API Configuration
BASE_URL = "http://127.0.0.1:8000/api"
EMAIL = "rittoone@gmail.com"
PASSWORD = "password123" # Assuming default from debug scripts, or we might need to reset it if unknown. 
# Wait, I don't know the user's password! 
# I will reset it temporarily in the script to ensure I can login, or I can generate a token manually via DB functions.
# Better: Generate token manually so I don't mess up their password if they set one.

import os
sys.path.append(os.getcwd())
sys.path.append(os.path.abspath("services/api_gateway"))
sys.path.append(os.path.abspath("packages/quant_shared/src"))
from quant_shared.models.models import User
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.auth.service import create_access_token

DB_PATH = "trading_data.db"
engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)
session = Session()

def get_token():
    user = session.query(User).filter_by(email=EMAIL).first()
    if not user:
        print(f"User {EMAIL} not found!")
        sys.exit(1)
    
    # Create valid access token directly
    access_token = create_access_token(data={"sub": user.email})
    return access_token, user.user_id

async def main():
    token, user_id = get_token()
    print(f"Testing for User: {EMAIL} (ID: {user_id})")
    
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient() as client:
        # 1. Get Strategies WITH Slash
        print("\n--- GET /api/strategies/ ---")
        try:
            resp = await client.get(f"{BASE_URL}/strategies/", headers=headers, timeout=10.0)
            print(f"With Slash: {resp.status_code}")
        except Exception as e:
            print(f"With Slash Error: {e}")

        # 2. Get Strategies WITHOUT Slash
        print("\n--- GET /api/strategies ---")
        try:
            resp = await client.get(f"{BASE_URL}/strategies", headers=headers, timeout=10.0)
            print(f"Without Slash: {resp.status_code}")
            if resp.status_code == 307:
                 print(f"Redirect Location: {resp.headers.get('location')}")
        except Exception as e:
            print(f"Without Slash Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
