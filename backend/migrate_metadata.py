import sys
import os
import sqlalchemy
from sqlalchemy import text

# Add current dir to path
sys.path.append(os.getcwd())

from src.database.connection import engine

def add_metadata_column():
    with engine.connect() as conn:
        try:
            # SQLite supports JSON type as TEXT, but using JSON type in SQLAlchemy maps to it.
            # In raw SQL for SQLite, we just add a column. SQLite calls it TEXT usually but allows JSON func.
            # We will use TEXT to be safe and simple for SQLite, SQLAlchemy handles serialization.
            # However, since we defined it as JSON in model, SQLAlchemy expects it.
            # Let's try adding it as JSON type if supported, else TEXT. 
            # SQLite 3.9+ supports JSON1 extension.
            
            sql = text("ALTER TABLE ml_reward_functions ADD COLUMN metadata_json JSON;")
            conn.execute(sql)
            print("Successfully added 'metadata_json' column to 'ml_reward_functions'.")
        except Exception as e:
            if "duplicate column" in str(e).lower():
                print("Column 'metadata_json' already exists. Skipping.")
            else:
                print(f"Error adding column: {e}")

if __name__ == "__main__":
    add_metadata_column()
