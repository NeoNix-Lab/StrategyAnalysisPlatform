# 🌉 Roadmap: Unificazione Export & API Platform

**Obiettivo:** Creare un'integrazione fluida tra il sistema di export della strategia C# (`StackedImbalanceStrategyDue`) e la piattaforma di analisi Python (`StrategyAnalysisPlatform`), permettendo un flusso dati automatizzato e analisi centralizzate.

## 🛠️ Fase 1: Allineamento Dati & Schema
**Obiettivo:** Garantire che i dati esportati dal C# siano perfettamente compatibili con il database della piattaforma.

- [x] **Verifica Schema Database**
    - [x] Confermare corrispondenza campi `Bars`, `Orders`, `Executions` tra C# (`SqliteExporter.cs`) e Python (`models.py`).
    - [x] Aggiungere eventuali campi mancanti (es. `liquidity_flag` in Executions se assente, o metadati extra).
- [x] **Versioning**
    - [x] Aggiungere campo `schema_version` nel DB SQLite esportato per gestire future migrazioni.

## 📥 Fase 2: Pipeline di Ingestione (ETL)
**Obiettivo:** Importare i dati generati dalla strategia (`.sqlite`) nel database centrale della piattaforma (`trading_data.db` / Postgres).

- [x] **Sviluppo Importer (`src/etl/import_sqlite.py`)**
    - [x] Lettura file SQLite di export.
    - [x] Mapping e validazione record (pydantic models).
    - [x] Upsert (Insert or Update) nel DB piattaforma per evitare duplicati.
    - [x] Gestione conflitti (es. stesso OrderID ma stato diverso).
- [x] **CLI Command**
    - [x] Creazione comando `python cli.py import --file <path>` per esecuzione manuale.
- [ ] **Watcher (Opzionale)**
    - [ ] Script che monitora una cartella e importa automaticamente i nuovi file `.sqlite`.

## 🔌 Fase 3: API Gateway & Upload
**Obiettivo:** Permettere l'invio dei dati direttamente via API, eliminando la necessità di spostare file manualmente.

- [x] **Endpoint Upload (`POST /api/ingest/upload`)**
    - [x] Accettazione file `.sqlite` o payload JSON compressi.
    - [x] Trigger asincrono del processo di importazione (Background Tasks).
- [x] **API Diretta (Future Proof)**
    - [x] Backend: Endpoint `POST /api/ingest/stream` implementato.
    - [x] Client C#: Modifica `SqliteExporter.cs` per inviare dati direttamente (Implementato `HttpExporter.cs` e `InMemoryExportBuffer.cs`).

## 🖥️ Fase 4: Integrazione Frontend
**Obiettivo:** Dare all'utente il controllo sul flusso dati direttamente dalla UI.

- [x] **Pagina "Data Management"**
    - [x] Drag & Drop area per caricare file `.sqlite` esportati.
    - [x] Storico importazioni (Data, Nome File, N. Record, Status) - *Placeholder UI created*.
- [x] **Data Quality Check**
    - [x] Report pre-importazione (es. "Trovati 50 nuovi ordini, 0 conflitti") - *Basic feedback implemented*.
- [x] **Dettaglio Trade**
    - [x] Pagina dedicata per visualizzare il grafico e i dettagli di una singola esecuzione (Chart + Entry/Exit markers).

## 📊 Fase 5: Trade Reconstruction & Analytics
**Obiettivo:** Una volta importati i dati grezzi (Orders/Executions), generare le metriche di alto livello.

- [x] **Trigger Trade Builder**
    - [x] Avvio automatico della ricostruzione trade (`TradeBuilder`) dopo ogni importazione.
    - [x] Notifica completamento ("Analisi aggiornata per strategia X").
- [x] **Verifica Coerenza**
    - [x] Check automatico: Implementato calcolo PnL interno (`TradeBuilder`). Confronto con PnL esterno non possibile (dato non esportato).

---

## 📝 Note Tecniche
- **Priorità:** Fase 1 e 2 sono bloccanti per l'utilizzo della piattaforma con i dati reali.
- **Performance:** L'importazione di file massivi deve avvenire in transazione unica o chunk per non bloccare il DB.
