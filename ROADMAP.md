# 🗺️ Roadmap: Strategy Analysis Platform

Questo documento unifica tutte le fasi di sviluppo, passate e future, organizzate in Sprint logici.

## ✅ Sprint 1: Fondamenta e Data Layer (Completato)
**Obiettivo:** Infrastruttura base per memorizzare e gestire i dati grezzi.

- [x] **Setup del Progetto**: Repository, Stack (Python/FastAPI/React), Database SQLite.
- [x] **Schema Database**: Tabelle `Bars`, `Orders`, `Executions`.
- [x] **Pipeline ETL Base**: Script importazione CSV/Parquet.

## ✅ Sprint 2: Unificazione C# & Trade Reconstruction (Completato)
**Obiettivo:** Integrazione con la strategia C# e logica di ricostruzione trade.

- [x] **C# Export**: Implementazione `IExporter`, `SqliteExporter`, `HttpExporter`.
- [x] **API Ingestion**: Endpoint `POST /api/ingest/stream` e `upload`.
- [x] **Trade Builder**: Algoritmo FIFO per ricostruire trade da esecuzioni.
- [x] **Data Persistence**: Logica "Gap Filling" per evitare duplicati (`import_sqlite.py`).

## ✅ Sprint 3: Analytics Core & Dashboard Base (Completato)
**Obiettivo:** Metriche essenziali e interfaccia utente.

- [x] **Metriche Trade**: PnL, MAE, MFE, Durata.
- [x] **Metriche Portafoglio**: Win Rate, Profit Factor, Drawdown, Equity Curve.
- [x] **Frontend (React)**:
    - Dashboard Overview (KPI, Equity Chart).
    - Pagina Trades (Lista filtrabile).
    - Dettaglio Trade (Grafico con marker Entry/Exit).
    - Pagina Data Management (Upload manuale).

## ✅ Sprint 4: Architecture Refactoring (Completato)
**Obiettivo:** Strutturare le esecuzioni in gerarchia `Strategy` -> `Run` per analisi comparative.

- [x] **Schema Design**:
    - [x] Tabella `Strategy` (ID, Name, Default Params).
    - [x] Tabella `StrategyRun` (ID, StrategyID, Params, DataRange).
    - [x] Migrazione `Trades`/`Orders` per includere `run_id`.
- [x] **Implementation**:
    - [x] Aggiornamento `models.py`.
    - [x] Aggiornamento Ingestion Logic per supportare i Run.
    - [x] Aggiornamento API/Frontend per filtrare per Run.

## � Sprint 5: Quant Lab & Advanced Analytics (In Corso)
**Obiettivo:** Funzionalità avanzate per ottimizzazione e robustezza.

- [ ] **Regime Detection**: Classificazione Trend/Range, Volatilità.
- [ ] **Parameter Lab**: Grid Search, Heatmaps, Sensitivity Analysis.
- [ ] **Stress Testing**: Monte Carlo, Scenarios (Spread, Slippage).
- [ ] **Setup Analysis**: Tagging manuale/automatico dei pattern (es. Breakout).

---

# 🔮 Appendice: Future Implementations
Idee e miglioramenti tecnici non ancora assegnati a uno sprint specifico.

## 🔄 Data Ingestion & Reliability
- **Smart Fallback**: API first -> Local DB fallback in caso di errore.
- **Directory Watcher**: Servizio background per import automatico file `.sqlite`.

## 📊 Analytics & Data Integrity
- **Advanced Trade Linking**: Gestione complessa di partial fills e scaling in/out.
- **Data Consistency**: Riconciliazione PnL Strategia vs PnL Piattaforma.

## 🖥️ Frontend Enhancements
- **Real-time Connection Status**: Indicatore heartbeat strategia.
- **Manual Trade Editing**: UI per correggere trade "rotti".
- **Reportistica**: Export PDF, Report comparativi.
