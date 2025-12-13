from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database.connection import init_db

# Routers
from src.api.routers import executions
from src.api.routers import bars
from src.api.routers import setups
from src.api.routers import ingest
from src.api.routers import strategies
from src.api.routers import runs

app = FastAPI(
    title="Strategy Analysis Platform API",
    description="Backend API for Quant Lab (Event-First)",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

app.include_router(executions.router, prefix="/api/executions", tags=["executions"])
app.include_router(bars.router, prefix="/api/bars", tags=["bars"])
app.include_router(setups.router, prefix="/api/setups", tags=["setups"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "Strategy Analysis Platform v2"}
