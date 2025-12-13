# Strategy Analysis Platform V2

## Overview
The Strategy Analysis Platform V2 is an event-first system designed for advanced algorithmic trading analytics. It unifies order flow export, persistence, and visualization into a seamless real-time dashboard.

### Core Philosophy: Event-First
Data is ingested as discrete events (Strategy Create, Instance Create, Run Start, Order, Execution, Bar) rather than bulk database dumps, ensuring real-time fidelity and robust data integrity.

## System Architecture

The repository is organized as a Monorepo:

*   **`backend/`**: Python-based REST API (FastAPI) & Data Ingestion Engine.
    *   Handles data persistence (SQLite/PostgreSQL).
    *   Processes `api/ingest/` events from exporters.
    *   Serves analysis endpoints to the frontend.
*   **`frontend/`**: Modern React Dashboard (Vite).
    *   Provides real-time visualization of PnL, Executions, and Volume.
    *   Manages Strategy -> Instance -> Run hierarchy.
*   **`exporters/`**: Connectors for Trading Platforms.
    *   **`quantower_template/`**: C# Example Strategy for Quantower that pushes events to the backend.
    *   **`StrategyExporter/`**: Core C# library for building custom exporters.
*   **`docs/`**: Detailed system documentation and architecture reference.

## Getting Started

### Prerequisites
*   **Python 3.10+**
*   **Node.js 18+**
*   **Quantower** (for running the exporter)

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
# Activate venv (Windows: .venv\Scripts\Activate)
pip install -r requirements.txt
python run_server.py
```
*Server runs on: http://127.0.0.1:8000*

### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
*Dashboard accessible at: http://localhost:5173*

### 3. Exporter Setup (Quantower)
1.  Open `exporters/quantower_template/StrategyExporterTemplate.sln` in Visual Studio.
2.  Restore NuGet packages.
3.  Build the solution.
4.  Run the strategy in Quantower.
    *   Ensure the `StartArguments` in `.csproj` match your backend port (default: 8000).

## Development Workflow
1.  **Modify Backend**: Edit schemas in `backend/src/api/schemas.py` and routers in `backend/src/api/routers/`.
2.  **Verify Data**: Use `backend/check_db.py` to inspect the database state.
3.  **Update Frontend**: Edit components in `frontend/src/`.
4.  **Debug Protocol**: Check `backend/src/api/routers/ingest.py` logs for event processing details.
