I cannot apply the requested change to the provided code document.

The instruction "Add 'auth' to the routers import and include it in the app.include_router calls" along with the provided "Code Edit" snippet (`from .api.routers import ...`, `app = FastAPI(...)`, `app.include_router(...)`) indicates that you are trying to modify a FastAPI application's main file (e.g., `main.py` or `app.py`).

However, the code document you provided:
```python
from src.database.connection import init_db
import os

def main():
    print("Avvio Strategy Analysis Platform...")
    
    # 1. Inizializza Database
    init_db()
    
    print("Setup completato. Il database è pronto per ricevere dati.")

if __name__ == "__main__":
    main()
```
is a simple Python script that initializes a database. It does not contain any FastAPI-related code, such as `FastAPI` imports, `app = FastAPI(...)` instantiation, or `app.include_router` calls.

Therefore, the elements you wish to modify (the `from .api.routers import ...` line and the `app.include_router` calls) do not exist in the provided document.

Please provide the correct code document (the FastAPI application file) if you wish to make this change.
