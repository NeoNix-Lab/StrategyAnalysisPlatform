# Strategy Analysis Platform V2

[![Backend CI](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/backend-ci.yml/badge.svg)](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/backend-ci.yml)
[![Frontend CI](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/frontend-ci.yml/badge.svg)](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/frontend-ci.yml)
[![.NET CI](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/dotnet-ci.yml/badge.svg)](https://github.com/NeoNix-Lab/StrategyAnalysisPlatform/actions/workflows/dotnet-ci.yml)

The Strategy Analysis Platform V2 is an event-first monorepo for algorithmic trading analytics. It ingests order-flow events, persists them, reconstructs trades/metrics, and exposes them through a real-time dashboard.

## Core Philosophy: Event-First
Every change in the trading lifecycle is sent as an event (strategy/instance/run creation, orders, executions, bars). This keeps the system consistent in real time and avoids bulky exports.

## Repository Layout
- `backend/`: FastAPI API and ingestion engine backed by SQLite by default (`trading_data.db` in the folder).
  - `src/api`: FastAPI app (`main.py`), Pydantic schemas, routers (`ingest`, `executions`, `bars`, `strategies`, `runs`, `setups`, `trades`) mounted under `/api`.
  - `src/database`: SQLAlchemy engine setup and models for strategies, instances, runs, orders, executions, trades, run/market series, bars, and ingest events.
  - `src/core`: Analytics helpers (`trade_service`, MAE/MFE computations).
  - `src/quantlab`: Metrics engine for reconstructing trades and regime detection utilities.
  - `src/services/analytics`: Pluggable analyzers orchestrated by `AnalyticsRouter` to populate `run.metrics_json`.
  - `src/etl`: Import helpers (e.g. `import_sqlite.py`).
  - Utility scripts: `run_server.py` (uvicorn entrypoint), `seed_data.py`, `migrate_db.py`, `check_db*.py`, `populate_dummy_data.py`, etc.
  - `tests/`: Pytest suite using in-memory SQLite fixtures (integration flow, trades, gap filling).
- `frontend/`: Vite + React dashboard.
  - `src/pages`: Dashboard widgets, executions monitor, data management, settings, setups, trades and reports views.
  - `src/components`, `src/hooks`, `src/context`: Layout shell, charts (Recharts, lightweight-charts), and shared UI/state helpers.
- `exporters/`: .NET 8 exporters for pushing events from Quantower.
  - `StrategyExporter/`: Reusable package with DTOs/services, packaged via `build_nuget.bat`.
  - `StrategyExporter.Tests/`: Basic unit tests for the exporter library.
  - `quantower_template/`: Runnable Quantower strategy template; adjust `StartArguments` in the `.csproj` to point to your backend host/port.
- `docs/`: Architecture, metrics, and exporter workflow references.

## Backend (FastAPI) Highlights
- Entrypoint: `backend/run_server.py` runs `src.api.main:app` on port 8000 with reload for development.
- Ingestion pipeline under `/api/ingest` handles event and batch endpoints for strategies/instances/runs, orders, executions, and bars. Data is persisted via SQLAlchemy with integrity checks and simple upserts.
- Analytics flow: `TradeService.rebuild_trades_for_run` reconstructs trades from executions using `quantlab.MetricsEngine`, then `services.analytics` computes P0/P1 metrics into `StrategyRun.metrics_json` with optional per-trade MAE/MFE calculations.
- Bars and market data: `RunSeries`/`Bar` capture run-scoped bars, `MarketSeries`/`MarketBar` store provider data with subscriptions.
- REST read endpoints surface executions, bars, strategies, runs, and trades for the frontend.

## Frontend (React) Highlights
- Router defined in `frontend/src/App.jsx` with a shared `Layout` shell.
- Main experiences live in `frontend/src/pages`: `Dashboard` (overview KPIs and charts), `Executions` (table and filters), `DataManagement`, `Settings`, and additional analysis pages (Setups, Trades, Reports, StressTest, Regime, Parameters).
- Styling is maintained in `App.css` and per-page CSS modules, using Recharts and lightweight-charts for plotting.

## Exporters (.NET) Highlights
- `StrategyExporter` library targets `net8.0` and provides DTOs plus HTTP services for posting events to `/api/ingest/...`.
- `quantower_template` is a ready-to-run strategy project; Visual Studio solution included. Update the `StartArguments` for your backend address and port before running in Quantower.


## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- .NET 8 SDK (for exporters)
- Quantower (to run the strategy template)

### Backend
```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\Activate
pip install -r requirements.txt
python run_server.py  # FastAPI on http://127.0.0.1:8000
```
The default storage is SQLite at `backend/trading_data.db`. Update `src/database/connection.py` if you want PostgreSQL or a different path.

### Frontend
```bash
cd frontend
npm install
npm run dev  # http://localhost:5173
```

### Exporter Template (Quantower)
1. Open `exporters/quantower_template/StrategyExporterTemplate.slnx` in Visual Studio.
2. Restore NuGet packages.
3. Adjust `StartArguments`/`StartProgram` in the `.csproj` to your Quantower install and backend port.
4. Build and run the strategy inside Quantower to stream events to the backend.

## Running Tests
- Backend: `cd backend && pytest`
- Frontend: `cd frontend && npm test`
- Exporter library: `cd exporters/StrategyExporter.Tests && dotnet test`

## Documentation
Supporting design notes and references live under `docs/`:
- `ARCHITECTURE.md`, `SystemV2_Reference.md`, `QuantowerExportWorkflowProposto.md`
- `Metrics.md`, `Analytics_Service_Refactor.md`, `DataManagement_Optimization_Plan.md`, `DBStructureProposto.md`

## Issue Tracking Automation
- `Issues/update_issue_record.py` parses each GitHub `issues` event and writes a per-issue JSON snapshot under `Issues/records`, keeps the `Issues/index.json` summary updated, and logs the event to `Issues/workflows/issue-events.log`.
- `.github/workflows/issue-tracking.yml` runs on every issue event, commits the generated files back to the repo, and therefore makes the repository its own issue database that workflows (and humans) can consume.
- The existing CI workflows (Backend, Frontend, .NET) already raise issues on failures; this automation ensures those issues and any manual edits are mirrored inside version control for tracking, audits, and downstream automation.
