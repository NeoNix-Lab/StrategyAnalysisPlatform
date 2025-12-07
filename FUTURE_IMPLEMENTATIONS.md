# 🚀 Future Implementations & Improvements

This document outlines planned features and architectural improvements for the Strategy Analysis Platform and its integration with the Trading Strategy.

## 🔄 Data Ingestion & Reliability

### Smart Fallback Mechanism (API vs Local DB)
**Current Status:** The strategy currently writes to a local SQLite file AND sends to the API simultaneously (if enabled).
**Goal:** Optimize data flow and ensure reliability without redundancy.
**Implementation Plan:**
1.  **Primary Channel (API):** Attempt to send data (Bars, Orders, Executions) via the HTTP API (`POST /api/ingest/stream`) for real-time availability.
2.  **Failure Detection:** Catch specific exceptions (Connection Refused, Timeout, 5xx Errors) from the HTTP client.
3.  **Fallback Channel (Local DB):** ONLY if the API fails, write the data to the local SQLite database/file.
    *   *Alternative:* Always write to a local "WAL" (Write Ahead Log) file for safety, but only mark as "Exported" if API confirms receipt.
4.  **Recovery:** Implement a mechanism to re-sync local data that wasn't sent to the API once the connection is restored.

### Directory Watcher Service
**Goal:** Automate the ingestion of files generated during API downtime or manual exports.
**Implementation Plan:**
-   Create a Python background service (`watchdog` library).
-   Monitor `MyDocuments/StrategyExports` for new `.sqlite` files.
-   Automatically trigger the `import_sqlite.py` logic when a file is closed/finished writing.

## 📊 Analytics & Data Integrity

### Advanced Trade Linking & Lifecycle
**Goal:** Robust reconstruction of complex trading behaviors.
**Implementation Plan:**
-   **Validation:** Verify `TradeId` consistency across partial fills, reversals, and scaling in/out scenarios.
-   **Visualization:** Create a "Trade Lifecycle" view in the frontend that groups all Orders and Executions by `TradeId`, showing the progression of the position over time.

### Data Consistency Checks
**Goal:** Ensure the platform's view matches the strategy's internal state.
**Implementation Plan:**
-   Export the Strategy's internal PnL and Position calculations alongside the raw executions.
-   Implement a "Reconciliation" task that compares Platform-calculated PnL vs Strategy-reported PnL and flags discrepancies.

## 🖥️ Frontend Enhancements

### Real-time Connection Status
**Goal:** Immediate feedback on system health.
**Implementation Plan:**
-   Add a "Strategy Connection" indicator in the Dashboard.
-   Use a heartbeat mechanism or track the "Last Data Received" timestamp to detect if the strategy has stopped sending data.

### Manual Trade Editing
**Goal:** Fix data issues manually.
**Implementation Plan:**
-   Allow users to manually edit or merge "broken" trades in the UI (e.g., linking an orphaned execution to a trade).

## 6. Strategy & Run Hierarchy (Architecture Refactoring)
**Obiettivo**: Strutturare le esecuzioni in modo gerarchico per permettere analisi comparative e storicizzazione precisa.

### Concetti Chiave
1.  **Strategy**: Entità unica definita da un ID e un set di parametri di default (JSON). Rappresenta la logica di trading (es. "StackedImbalanceStrategy").
2.  **StrategyRun**: Una specifica istanza di esecuzione di una Strategia.
    - Ha un `run_id` univoco.
    - È legata a una `Strategy`.
    - Ha un set specifico di **Parametri** usati per quella corsa.
    - È legata a un **Data Range** specifico (es. "Symbol: EURUSD, Timeframe: 1m, Range: 2023-01-01 to 2023-12-31").
3.  **Gerarchia Dati**:
    - `Strategy` -> `StrategyRun` -> `Trades` / `Orders`.
    - Ogni Trade e Ordine deve appartenere a un `run_id`.

### Benefici
- **Confronto Parametri**: Possibilità di confrontare due Run della stessa strategia con parametri diversi (A/B Testing).
- **Riproducibilità**: Sapere esattamente su quali dati e con quali parametri è stato generato un risultato.
- **UI Navigation**: Selezionare prima la Strategia, poi il Run specifico, e infine vedere i dettagli.
