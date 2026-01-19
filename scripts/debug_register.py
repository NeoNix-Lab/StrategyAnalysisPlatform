import sys
import os

# Add services/api_gateway/src to path
sys.path.append(os.path.join(os.getcwd(), 'services', 'api_gateway', 'src'))

from quant_shared.models.connection import get_db, init_db
from quant_shared.models.models import User
from auth import service
from pydantic import ValidationError

def debug_registration():
    print("🚀 Debugging Registration...")
    init_db()
    db = next(get_db())
    
    email = "rittoone@gmail.com"
    password = "testpassword123"
    
    # 1. Check if user exists
    print(f"Checking if {email} exists...")
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        print(f"❌ User already exists! ID: {existing.user_id}")
        # This explains the 400 error if the UI received it
    else:
        print("✓ User does not exist. Attempting creation via service...")
        try:
            # 2. Try to create user using the service function
            new_user = service.create_user(db, email=email, password=password)
            print(f"✅ User created successfully! ID: {new_user.user_id}")
        except Exception as e:
            print(f"❌ Creation failed with error: {e}")
            import traceback
            with open("debug_error.log", "w") as f:
                traceback.print_exc(file=f)

if __name__ == "__main__":
    debug_registration()
