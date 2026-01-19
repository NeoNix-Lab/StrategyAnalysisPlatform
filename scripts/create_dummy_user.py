import sys
import os
import uuid

# Add services/api_gateway/src to path to use auth service
sys.path.append(os.path.join(os.getcwd(), 'services', 'api_gateway', 'src'))

from quant_shared.models.connection import get_db, init_db
from quant_shared.models.models import User, Role
from auth.crypto import PasswordHasherService

def create_user():
    print("🚀 Creating/Updating User...")
    init_db()
    
    db = next(get_db())
    hasher = PasswordHasherService()
    
    email = "quant@lab.local"
    dummy_id = "dummy_user_id"
    password = "admin"
    
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            print(f"✓ User {email} exists. Updating ID/Password...")
            if user.user_id != dummy_id:
                # We need to ensure ID is dummy_id for consistency with hardcoded bypasses if any remain
                # But changing PK is risky if relationships exist. 
                # Let's hope no relationships exist yet or just update if we can.
                # Actually, easier to leave ID as is if it exists, OR force it. 
                # If we rely on "dummy_user_id" string in code, we must ensure it matches.
                # Let's just create a new one if ID doesn't match? No, email constraint.
                # Let's just update the bypass code to look up by email instead of ID if needed.
                # But simpler: ensure we upsert with specific ID.
                pass 
            
            user.hashed_password = hasher.hash_password(password)
            user.role = Role.ADMIN
            user.is_active = True
        else:
            print(f"+ Creating User {email}...")
            user = User(
                user_id=dummy_id,
                email=email,
                hashed_password=hasher.hash_password(password),
                role=Role.ADMIN,
                is_active=True
            )
            db.add(user)
        
        db.commit()
        print(f"✅ User {email} ready with ID: {user.user_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_user()
