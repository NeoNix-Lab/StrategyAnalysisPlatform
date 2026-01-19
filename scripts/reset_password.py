import sys
import os

# Add services/api_gateway/src to path
sys.path.append(os.path.join(os.getcwd(), 'services', 'api_gateway', 'src'))

from quant_shared.models.connection import get_db, init_db
from quant_shared.models.models import User
from auth.service import hasher

def reset_password(email, new_password):
    print(f"🔄 Resetting password for {email}...")
    init_db()
    db = next(get_db())
    
    user = db.query(User).filter(User.email == email).first()
    if user:
        hashed = hasher.hash_password(new_password)
        user.hashed_password = hashed
        db.commit()
        print(f"✅ Password reset successfully to: {new_password}")
        print(f"🔑 New hash prefix: {hashed[:20]}...")
    else:
        print(f"❌ User {email} not found.")

if __name__ == "__main__":
    reset_password("rittoone@gmail.com", "password123")
