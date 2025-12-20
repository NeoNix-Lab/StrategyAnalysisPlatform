import sys
import os

# Ensure backend root is in path
sys.path.append(os.getcwd())

from src.database.connection import engine
from src.database.models import Base, User, UserSettings, ApiKey

def init():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created.")

if __name__ == "__main__":
    init()
