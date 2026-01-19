import sys
import os

# Add services/api_gateway/src to path just in case, though quant_shared should be available
sys.path.append(os.path.join(os.getcwd(), 'services', 'api_gateway', 'src'))

try:
    from quant_shared.models.connection import get_db
    from quant_shared.models.models import User
except ImportError:
    # Fallback for direct execution if package structure requires it
    sys.path.append(os.path.join(os.getcwd(), 'packages', 'quant_shared', 'src'))
    from quant_shared.models.connection import get_db
    from quant_shared.models.models import User

def list_users():
    try:
        db = next(get_db())
        users = db.query(User).all()
        
        print("\n=== Registered Users ===")
        print(f"{'ID':<38} | {'Email':<30} | {'Role':<10} | {'Active'}")
        print("-" * 90)
        
        for user in users:
            print(f"{user.user_id:<38} | {user.email:<30} | {str(user.role.value):<10} | {user.is_active}")
            
        print(f"\nTotal Users: {len(users)}\n")
        
    except Exception as e:
        print(f"Error listing users: {e}")

if __name__ == "__main__":
    list_users()
