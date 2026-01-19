import sys
import os

# Add services/api_gateway/src to path
sys.path.append(os.path.join(os.getcwd(), 'services', 'api_gateway', 'src'))

from quant_shared.models.connection import get_db, init_db
from quant_shared.models.models import User

def delete_user(email):
    print(f"🗑️ Deleting user {email}...")
    init_db()
    db = next(get_db())
    
    user = db.query(User).filter(User.email == email).first()
    if user:
        db.delete(user)
        db.commit()
        print(f"✅ User {email} deleted successfully.")
    else:
        print(f"ℹ️ User {email} not found.")

if __name__ == "__main__":
    delete_user("rittoone@gmail.com")
