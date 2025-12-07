from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.database.connection import init_db
from src.api.routers import trades, bars, experiments, stress, setups, ingest, strategies

app = FastAPI(
    title="Strategy Analysis Platform API",
    description="Backend API for Quant Lab",
    version="1.0.0"
)

# Configurazione CORS per permettere al frontend (React) di comunicare
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000"], # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inizializzazione DB all'avvio
@app.on_event("startup")
def on_startup():
    init_db()

# Registrazione Routers
app.include_router(trades.router, prefix="/api/trades", tags=["trades"])
app.include_router(bars.router, prefix="/api/bars", tags=["bars"])
app.include_router(experiments.router, prefix="/api/experiments", tags=["experiments"])
app.include_router(stress.router, prefix="/api/stress", tags=["stress"])
app.include_router(setups.router, prefix="/api/setups", tags=["setups"])
app.include_router(ingest.router, prefix="/api/ingest", tags=["ingest"])
app.include_router(strategies.router, prefix="/api/strategies", tags=["strategies"])

@app.get("/health")
def health_check():
    return {"status": "ok", "system": "Strategy Analysis Platform"}
