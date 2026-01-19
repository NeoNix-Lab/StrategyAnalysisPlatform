import sys
import os

# Add services/api_gateway/src to path
sys.path.append(os.path.join(os.getcwd(), 'services', 'api_gateway', 'src'))

from quant_shared.models.connection import get_db, init_db
from quant_shared.models.models import User
from auth import service
import traceback

def debug_login():
    print("🚀 Debugging Login...")
    init_db()
    db = next(get_db())
    
    email = "debug_login_user@example.com"
    password = "testpassword123"
    
    # Clean up potentially existing user
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        db.delete(existing)
        db.commit()
    
    print("1. Creating user...")
    try:
        user = service.create_user(db, email=email, password=password)
        print(f"✅ User created. Hash: {user.hashed_password[:20]}...")
    except Exception:
        traceback.print_exc()
        return

    print("2. Attempting authentication...")
    try:
        authenticated_user = service.authenticate_user(db, email, password)
        if authenticated_user:
            print("✅ Authentication successful!")
        else:
            print("❌ Authentication failed (returned False/None).")
            # Let's inspect why
            from auth.service import hasher
            print(f"   Verify result: {hasher.verify_password(password, user.hashed_password)}")
    except Exception as e:
        print(f"❌ Authentication crashed: {e}")
        with open("debug_login_error.log", "w") as f:
            traceback.print_exc(file=f)
        traceback.print_exc()

if __name__ == "__main__":
    debug_login()
