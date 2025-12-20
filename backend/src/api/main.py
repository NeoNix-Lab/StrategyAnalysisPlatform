from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database.connection import init_db
import sys
import asyncio

# Fix for Windows "too many file descriptors in select()" error
# This switches the event loop to Proactor (IOCP) which supports >> 512 connections.
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Routers
from src.api.routers import executions
from src.api.routers import bars
from src.api.routers import setups
from src.api.routers import ingest
from src.api.routers import strategies
from src.api.routers import runs
from src.api.routers import trades
from src.api.routers import metrics
from src.api.routers import auth
from src.api.routers import training
from src.api.routers import datasets
from src.api.routers import ml_studio

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
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(training.router, prefix="/api/training", tags=["training"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(ml_studio.router, prefix="/api", tags=["ml-studio"]) # Fix inclusion

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "Strategy Analysis Platform v2"}
