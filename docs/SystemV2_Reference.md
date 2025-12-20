# System V2 Reference Guide

Questo documento riassume la nuova struttura del Database e degli Endpoint API implementata nella versione "Event-First" (V2).

## 1. Database Structure (`src/database/models.py`)

L'architettura segue la gerarchia: **Strategy -> Instance -> Run -> [Orders, Executions, Events]**.

### Core Hierarchy
| Tabella | Descrizione | Relazioni Principali |
| :--- | :--- | :--- |
| **`strategies`** | Definizione logica, indipendente dai parametri. | `1-N` con `strategy_instances` |
| **`strategy_instances`** | Configurazione specifica (Parametri, Simboli, Account). | `N-1` con `strategies`, `1-N` con `strategy_runs` |
| **`strategy_runs`** | Singola sessione di esecuzione (Live/Backtest) legata a un'Istanza. | `N-1` con `strategy_instances` |

### Trading Data
| Tabella | Descrizione | Note |
| :--- | :--- | :--- |
| **`orders`** | Ordini inviati. Supporta OCO e Position Impact. | `status`, `position_impact` (OPEN/CLOSE/...), `client_tag`. Linkata a `run_id`. |
| **`executions`** | Fills effettivi. Sostituisce la tabella `trades` aggregata. | `price`, `quantity`, `fee`, `liquidity`. Linkata a `order_id` e `run_id`. |
| **`order_oco_groups`** | Raggruppamenti logici per ordini OCO/Bracket. | Collega più `orders` tramite `order_oco_links`. |

### Time Series & Telemetry
| Tabella | Descrizione | Note |
| :--- | :--- | :--- |
| **`run_series`** | Metadati della serie temporale (Simbolo, TF). | Definisce cosa contiene la serie (es. `has_volumetric`). |
| **`bars`** | Dati OHLCV + Payload Volumetrico. | Colonna `volumetric_json` per dati futuri (POC, Delta). |
| **`ingest_events`** | Log raw di tutti gli eventi ricevuti. | Utile per debugging e replay ("Event Sourcing"). |

---

## 2. API Endpoints (`src/api/routers/`)

### Ingestion (Write) - `routers/ingest.py`
Endpoint dedicati alla ricezione eventi in tempo reale dal C# Exporter.

- `POST /api/ingest/event/strategy_create` - Crea/Aggiorna definizione Strategia.
- `POST /api/ingest/event/instance_create` - Registra una configurazione (Istanza).
- `POST /api/ingest/event/run_start` - Avvia una nuova Run.
- `POST /api/ingest/event/order` - Inserisce o aggiorna un Ordine.
- `POST /api/ingest/event/execution` - Registra un eseguito (Fill).
- `POST /api/ingest/event/bar` - Aggiunge una barra alla serie temporale.

### Data Retrieval (Read)

**Strategies & Configuration (`routers/strategies.py`)**
- `GET /api/strategies/` - Lista tutte le strategie.
- `GET /api/strategies/{id}` - Dettaglio singola strategia.
- `GET /api/strategies/{id}/instances` - Lista configurazioni usate per quella strategia.

**Runs (`routers/runs.py`)**
- `GET /api/runs/instance/{instance_id}` - Cronologia esecuzioni per una configurazione.
- `GET /api/runs/{run_id}` - Dettagli e metriche aggregate della Run.

**Trading Data (`routers/executions.py`)**
- `GET /api/executions/run/{run_id}` - Lista eseguiti raw (usata dal Frontend per calcoli/lista).

**Market Data (`routers/bars.py`)**
- `GET /api/bars/?run_id=...&symbol=...` - Serie storica (candele) per i grafici.

---

## 3. Note per lo Sviluppo

- **PnL Calculation**: Attualmente il backend restituisce gli eseguiti "grezzi". Il calcolo del PnL "Closed Trade" (Entry vs Exit) deve essere re-implementato o nel Backend (nuovo modulo analytics) o nel Frontend.
- **Volumetric Data**: La struttura DB è pronta (`volumetric_json`), ma l'exporter C# deve essere esteso per popolarla.
