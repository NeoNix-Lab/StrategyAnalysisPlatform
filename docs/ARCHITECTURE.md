# Architettura del Progetto StrategyAnalysisPlatform

Questo documento descrive l'architettura ad alto livello della piattaforma di analisi delle strategie di trading.

## Panoramica
Il sistema è progettato per raccogliere, archiviare e analizzare i dati generati da strategie di trading automatizzato eseguite sulla piattaforma **Quantower**. È composto da tre parti principali: un componente di esportazione dati (strategy template), un backend di analisi centralizzato e una dashboard frontend per la visualizzazione.

## Diagramma Architetturale (Concettuale)

```mermaid
graph TD
    subgraph "Data Generation (Quantower)"
        QT[StrategyExporterTemplate] -->|HTTP POST (Live)| API
        QT -->|SQLite File (Backtest)| ETL
    end

    subgraph "Backend (StrategyAnalysisPlatform)"
        API[FastAPI Server] --> DB[(SQL Database)]
        ETL[ETL / Import Scripts] --> DB
        DB <--> Models[SQLAlchemy Models]
    end

    subgraph "Frontend (StrategyAnalysisDashboard)"
        Dashboard[React Dashboard] -->|REST Calls| API
    end
```

## Componenti Principali

### 1. Data Source & Ingestion (C# / Export)
Il punto di ingresso dei dati, situato nel progetto **`StrategyExporterTemplate`**.
- **Piattaforma**: Quantower.
- **Funzionamento**:
  - Utilizza la libreria `StrategyExporter` per mappare eventi di trading (Ordini, Eseguiti) in DTOs.
  - **Live Mode**: Invia dati in tempo reale via HTTP POST.
  - **Backtest/Batch Mode**: Archivia i dati su file locali per importazione successiva.

### 2. Struttura Dati Esportabile
I dati vengono trasferiti utilizzando specifiche strutture (DTO).
#### OrderDto
Rappresenta un ordine inviato al mercato.
- `RunId`: Identificativo univoco della sessione.
- `StrategyId`, `OrderId`, `Symbol`, `AccountId`.
- `Side`: (BUY/SELL).
- `OrderType`: (MARKET, LIMIT, STOP, ecc.).
- `Quantity`, `Price`, `StopPrice`.
- `Status`: (NEW, FILLED, CANCELED, REJECTED).
- `SubmitTime`.

#### ExecutionDto (Trade)
Rappresenta un'esecuzione avvenuta (fill).
- `ExecutionId`, `OrderId`.
- `Price`, `Quantity`.
- `Fee`: Commissioni pagate.
- `ExecTime`.

#### BarDto (Estensione Volumetrica)
Rappresenta la barra di prezzo. In aggiunta ai classici dati OHLCV, la struttura è predisposta per includere dati volumetrici dettagliati (future implementation):
- **Core**: `Open`, `High`, `Low`, `Close`, `Volume`.
- **Volumetric Data (Futuro)**:
  - `BidVolume`: Volume scambiato sul Bid.
  - `AskVolume`: Volume scambiato sull'Ask.
  - `Delta`: Differenza netta tra AskVolume e BidVolume.
  - `POC (Point of Control)`: Livello di prezzo con maggior volume nella barra.
  - `TotalTrades`: Numero totale di tick/trade.

### 3. Backend (Python / FastAPI)
Il cuore della piattaforma (`StrategyAnalysisPlatform`).
- **Tech Stack**: Python, FastAPI, SQLAlchemy, SQLite (o PostgreSQL in futuro).
- **Core Modules**:
  - **`api/`**: Endpoint REST (`ingest.py`, `strategies.py`).
  - **`database/`**: Modelli SQL (`models.py`) che specchiano le strutture dati sopra descritte.
  - **`etl/`**: Script helper (`import_sqlite.py`) per caricare dati storici generati da Quantower.

### 4. Frontend (React / Vite)
L'interfaccia utente (`StrategyAnalysisDashboard`) ristrutturata per la **V2 Event-First**.
- **Hierarchy**: Strategy -> Instance -> Run.
- **Pages**: 
    - `Dashboard`: KPI in tempo reale (Esecuzioni, Volume).
    - `Executions`: Log grezzo degli eventi.
    - `DataManagement`: Stato del sistema e Data Pipeline.
- **Legacy (Disabled)**: Funzionalità complesse (`Parameters`, `Efficiency`) disabilitate in attesa del modulo Analytics.


## Flusso dei Dati
1. La strategia in Quantower genera eventi (`OnTradeAdded`, `OnOrderAdded`).
2. `StrategyExporterTemplate` converte gli eventi in DTO e li invia al Backend.
3. Il Backend salva i dati:
   - Ordini ed Eseguiti vengono collegati a una `StrategyRun`.
   - Eventuali dati volumetrici nelle barre vengono parsati e archiviati (JSON o colonne dedicate).
4. Il Frontend interroga l'API per mostrare grafici di equity, liste ordini e analisi volumetriche (in futuro).
