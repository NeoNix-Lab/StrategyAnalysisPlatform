from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from quant_shared.models.connection import init_db, DB_PATH
from quant_shared.utils.logger import get_logger
import sys
import os
import asyncio
import time

# Initialize Logger
logger = get_logger("api_gateway")

# Fix for Windows "too many file descriptors in select()" error
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Routers
from .routers import executions
from .routers import bars
from .routers import setups
from .routers import ingest
from .routers import strategies
from .routers import runs
from .routers import trades
from .routers import regime
from .routers import metrics
from .routers import auth
from .routers import training
from .routers import ml_studio
from .routers import ml_studio
from .routers import datasets
from .routers import system

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

@app.middleware("http")
async def log_requests(request: Request, call_next):
    import uuid
    
    # 1. Trace ID Extraction/Generation
    trace_id = request.headers.get("X-Trace-Id")
    if not trace_id:
        trace_id = str(uuid.uuid4())
    
    # 2. Add to context (Thread-local storage would be better for extensive usage, 
    # but for now we just log it).
    # Ideally, we would set this in a contextvar for the logger to pick up automatically.
    
    start_time = time.time()
    
    # 3. Process Request
    try:
        response = await call_next(request)
    except Exception as e:
        # In case of unhandled error, we still want to log standard info
        # The exception handler usually catches this, but middleware sees it if it bubbles up.
        # For now, let it bubble, FastAPI default handler will manage 500.
        raise e
        
    process_time = time.time() - start_time
    
    # 4. Inject Trace ID into Response Headers
    response.headers["X-Trace-Id"] = trace_id
    
    # 5. Log with Trace ID
    # We use extra dict if our logger supports it, or just append to message
    # Since our logger is simple, we append.
    logger.info(f"[{trace_id}] {request.method} {request.url.path} - {response.status_code} - {process_time:.4f}s")
    
    return response

@app.on_event("startup")
def on_startup():
    logger.info("Starting API Gateway Service...")
    logger.info(f"Environment TRADING_DB_PATH: {os.getenv('TRADING_DB_PATH')}")
    logger.info(f"Actual DB_PATH used: {DB_PATH}")
    init_db()

app.include_router(executions.router, prefix="/api/executions", tags=["executions"])
app.include_router(bars.router, prefix="/api/bars", tags=["bars"])
app.include_router(setups.router, prefix="/api/setups", tags=["setups"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])
app.include_router(runs.router, prefix="/api/runs", tags=["runs"])
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(metrics.router, prefix="/api/metrics", tags=["metrics"])
app.include_router(regime.router, prefix="/api/regime", tags=["regime"])
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(training.router, prefix="/api/training", tags=["training"])
app.include_router(ml_studio.router, prefix="/api/ml/studio", tags=["ml_studio"])
app.include_router(datasets.router, prefix="/api/datasets", tags=["datasets"])
app.include_router(system.router, prefix="/api/system", tags=["system"])

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "Strategy Analysis Platform v2"}
