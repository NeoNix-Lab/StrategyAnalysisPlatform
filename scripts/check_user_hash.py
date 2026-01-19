import sys
import os

# Add services/api_gateway/src to path
sys.path.append(os.path.join(os.getcwd(), 'services', 'api_gateway', 'src'))

from quant_shared.models.connection import get_db, init_db
from quant_shared.models.models import User

def check_user_hash(email):
    print(f"🔍 Checking user {email}...")
    init_db()
    db = next(get_db())
    
    user = db.query(User).filter(User.email == email).first()
    if user:
        print(f"✅ User found: {user.user_id}")
        print(f"🔑 Hash: {user.hashed_password}")
        if user.hashed_password.startswith("$pbkdf2"):
             print("ℹ️ Algorithm: PBKDF2 (Correct)")
        elif user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2a$"):
             print("⚠️ Algorithm: BCRYPT (Could be problematic if library broken)")
        else:
             print("❓ Algorithm: Unknown/Other")
    else:
        print(f"❌ User {email} NOT found.")

if __name__ == "__main__":
    check_user_hash("rittoone@gmail.com")
