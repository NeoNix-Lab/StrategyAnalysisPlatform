import sys
import os

# Add services/api_gateway/src to path to import models
sys.path.append(os.path.join(os.getcwd(), 'services', 'api_gateway', 'src'))

from quant_shared.models.connection import get_db
from quant_shared.models.models import User

db = next(get_db())
user = db.query(User).filter(User.email == "quant@lab.local").first()

if user:
    print(f"User found: {user.user_id}")
else:
    print("User not found")
