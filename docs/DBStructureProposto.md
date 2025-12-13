Perfetto: se lo scopo è **comparare strategie/istanze/run** e mantenere **tracciabilità completa** (run → ordini → eseguiti, più relazioni OCO e “position impact type”, più eventuale persistenza della serie temporale), allora conviene progettare il DB “event-first” ma con entità normalizzate, e con **chiavi stabili** (quelle di Quantower + i tuoi UUID) come già emerge dalla tua architettura e DTO .

Struttura Proposta SQLite **solida e scalabile**, pensata per:

* correlare **Strategy → StrategyInstance → StrategyRun**
* correlare **Run → Orders → Executions**
* gestire **OCO** e **ordine “position impact”** (open/close/reduce/reverse/unknown)
* archiviare (se serve) **bar series** e opzionalmente “payload volumetrico”
* supportare analisi (equity, pnl, slippage, fill ratio, latency, etc.) con indici adeguati

---

## 1) Entità principali e relazioni (ER mentale)

* **strategies**: definizione logica (nome/versione/provenienza)
* **strategy_instances**: configurazioni concrete (parametri, simbolo/i, TF, account, settaggi)
* **strategy_runs**: una singola esecuzione (backtest o live), con finestra temporale, ambiente, risultati aggregati
* **orders**: ordini emessi durante una run
* **executions**: fill/eseguiti legati agli ordini
* **order_oco_groups** + **order_oco_links**: per raggruppare ordini in OCO (anche multi-leg)
* **run_series** + **bars**: archivio della serie temporale (se non già disponibile altrove)

---

## 2) DDL SQLite proposto (core)

### 2.1 Strategies / Instances / Runs

```sql
PRAGMA foreign_keys = ON;

-- Strategia "logica" (template / repo / vendor / ecc.)
CREATE TABLE strategies (
  strategy_id        TEXT PRIMARY KEY,           -- UUID (tuo)
  name               TEXT NOT NULL,
  version            TEXT,
  vendor             TEXT,                       -- es. Quantower / custom / community
  source_ref         TEXT,                       -- repo url, commit hash, package id
  created_utc        TEXT NOT NULL,
  notes              TEXT
);

-- Istanza: parametri e contesto di esecuzione "configurato"
CREATE TABLE strategy_instances (
  instance_id        TEXT PRIMARY KEY,           -- UUID (tuo)
  strategy_id        TEXT NOT NULL,
  instance_name      TEXT,
  parameters_json    TEXT NOT NULL,              -- snapshot parametri (json)
  symbol             TEXT,                       -- se single-symbol
  symbols_json       TEXT,                       -- se multi-symbol
  timeframe          TEXT,                       -- es "1m", "5m", "tick", "range"
  account_id         TEXT,                       -- id account (stringa Quantower)
  venue              TEXT,                       -- exchange/broker
  created_utc        TEXT NOT NULL,
  FOREIGN KEY(strategy_id) REFERENCES strategies(strategy_id)
);

-- Run: una singola esecuzione (live/backtest)
CREATE TABLE strategy_runs (
  run_id             TEXT PRIMARY KEY,           -- UUID (tuo) = RunId dei DTO :contentReference[oaicite:1]{index=1}
  instance_id        TEXT NOT NULL,
  run_type           TEXT NOT NULL,              -- 'BACKTEST'|'LIVE'|'PAPER'|'REPLAY'
  start_utc          TEXT NOT NULL,
  end_utc            TEXT,
  status             TEXT NOT NULL,              -- 'RUNNING'|'COMPLETED'|'FAILED'|'CANCELED'
  engine_version     TEXT,                       -- versione Quantower / exporter / backend
  data_source        TEXT,                       -- feed / file / provider
  initial_balance    REAL,
  base_currency      TEXT,
  metrics_json       TEXT,                       -- snapshot metriche aggregate (json)
  created_utc        TEXT NOT NULL,
  FOREIGN KEY(instance_id) REFERENCES strategy_instances(instance_id)
);

CREATE INDEX idx_runs_instance_time ON strategy_runs(instance_id, start_utc);
CREATE INDEX idx_runs_type_status  ON strategy_runs(run_type, status);
```

---

### 2.2 Orders / Executions (con position impact + correlazioni)

```sql
-- Ordini
CREATE TABLE orders (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id              TEXT NOT NULL,
  strategy_id         TEXT,                      -- ridondanza utile per query veloci
  order_id            TEXT NOT NULL,             -- OrderId Quantower :contentReference[oaicite:2]{index=2}
  parent_order_id     TEXT,                      -- per legami parent/child (bracket)
  symbol              TEXT NOT NULL,
  account_id          TEXT,
  side                TEXT NOT NULL,             -- BUY/SELL
  order_type          TEXT NOT NULL,             -- MARKET/LIMIT/STOP/...
  tif                 TEXT,                      -- TimeInForce se disponibile
  quantity            REAL NOT NULL,
  price               REAL,
  stop_price          REAL,
  status              TEXT NOT NULL,             -- NEW/FILLED/CANCELED/REJECTED...
  submit_utc          TEXT NOT NULL,
  update_utc          TEXT,                      -- ultimo update
  client_tag          TEXT,                      -- tag custom lato strategy
  position_impact     TEXT NOT NULL DEFAULT 'UNKNOWN',
  -- es: 'OPEN'|'CLOSE'|'REDUCE'|'REVERSE'|'UNKNOWN'
  extra_json          TEXT,                      -- dump eventuale extra DTO
  UNIQUE(run_id, order_id),
  FOREIGN KEY(run_id) REFERENCES strategy_runs(run_id)
);

CREATE INDEX idx_orders_run_time   ON orders(run_id, submit_utc);
CREATE INDEX idx_orders_orderid    ON orders(order_id);
CREATE INDEX idx_orders_symbol     ON orders(symbol);
CREATE INDEX idx_orders_status     ON orders(status);

-- Eseguiti/Fills
CREATE TABLE executions (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id              TEXT NOT NULL,
  execution_id        TEXT NOT NULL,             -- ExecutionId :contentReference[oaicite:3]{index=3}
  order_id            TEXT NOT NULL,             -- OrderId :contentReference[oaicite:4]{index=4}
  exec_utc            TEXT NOT NULL,
  price               REAL NOT NULL,
  quantity            REAL NOT NULL,
  fee                 REAL,
  fee_currency        TEXT,
  liquidity           TEXT,                      -- MAKER/TAKER se disponibile
  extra_json          TEXT,
  UNIQUE(run_id, execution_id),
  FOREIGN KEY(run_id) REFERENCES strategy_runs(run_id)
);

CREATE INDEX idx_exec_run_time     ON executions(run_id, exec_utc);
CREATE INDEX idx_exec_order        ON executions(run_id, order_id);
```

Nota pratica: in `executions` *non* metto FK verso `orders(id)` perché tu hai `order_id` stringa come chiave esterna naturale; in ingest live potresti ricevere execution prima dell’order (dipende dal flusso). Con `(run_id, order_id)` indicizzato, la join resta veloce e non “spacchi” l’ingest.

---

## 3) OCO: gruppi e membership + metadati “impact”

Qui l’obiettivo è: “questi ordini sono in relazione OCO” e vuoi anche capire **che ruolo hanno** (TP/SL/Entry/Exit) e il loro impatto posizione.

```sql
-- Gruppo OCO (un set di ordini che si cancellano a vicenda)
CREATE TABLE order_oco_groups (
  oco_group_id       TEXT PRIMARY KEY,          -- UUID tuo
  run_id             TEXT NOT NULL,
  created_utc        TEXT NOT NULL,
  label              TEXT,                      -- es "Bracket#12"
  extra_json         TEXT,
  FOREIGN KEY(run_id) REFERENCES strategy_runs(run_id)
);

CREATE INDEX idx_oco_run ON order_oco_groups(run_id);

-- Membership ordine ↔ gruppo OCO
CREATE TABLE order_oco_links (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id             TEXT NOT NULL,
  oco_group_id       TEXT NOT NULL,
  order_id           TEXT NOT NULL,             -- OrderId Quantower
  oco_role           TEXT,                      -- 'TP'|'SL'|'ENTRY'|'EXIT'|'HEDGE'|...
  position_impact    TEXT NOT NULL DEFAULT 'UNKNOWN',
  UNIQUE(run_id, oco_group_id, order_id),
  FOREIGN KEY(run_id) REFERENCES strategy_runs(run_id),
  FOREIGN KEY(oco_group_id) REFERENCES order_oco_groups(oco_group_id)
);

CREATE INDEX idx_oco_links_order ON order_oco_links(run_id, order_id);
```

In questo modo puoi:

* risalire rapidamente da un ordine al suo gruppo OCO
* confrontare ruoli e impatti dei legs (es. TP = CLOSE, SL = CLOSE, Entry = OPEN)
* supportare anche casi “strani” (OCO non solo TP/SL)

---

## 4) Serie temporale: archiviare solo se serve (e senza esplodere il DB)

Dato che vuoi “archiviare per ogni run i dati dettagliati della serie temporale se questi non sono già presenti”, io farei due livelli:

* **run_series**: descrive la serie (simbolo, tf, sorgente, “full snapshot?”)
* **bars**: le barre (OHLCV + eventuale volumetrico come JSON)

```sql
CREATE TABLE run_series (
  series_id          TEXT PRIMARY KEY,          -- UUID tuo
  run_id             TEXT NOT NULL,
  symbol             TEXT NOT NULL,
  timeframe          TEXT NOT NULL,              -- '1m','5m','tick','range',...
  source             TEXT,                       -- provider/file/cache
  start_utc          TEXT,
  end_utc            TEXT,
  has_volumetric     INTEGER NOT NULL DEFAULT 0, -- 0/1
  created_utc        TEXT NOT NULL,
  UNIQUE(run_id, symbol, timeframe),
  FOREIGN KEY(run_id) REFERENCES strategy_runs(run_id)
);

CREATE INDEX idx_series_run ON run_series(run_id);

CREATE TABLE bars (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  series_id          TEXT NOT NULL,
  ts_utc             TEXT NOT NULL,
  open               REAL NOT NULL,
  high               REAL NOT NULL,
  low                REAL NOT NULL,
  close              REAL NOT NULL,
  volume             REAL,
  -- volumetrico esteso: bid/ask/delta/poc/trades ecc. :contentReference[oaicite:5]{index=5}
  volumetric_json    TEXT,
  UNIQUE(series_id, ts_utc),
  FOREIGN KEY(series_id) REFERENCES run_series(series_id)
);

CREATE INDEX idx_bars_series_time ON bars(series_id, ts_utc);
```

Regola pratica: se gestirai tick / footprint / volumetrico molto pesante, SQLite può reggere ma conviene:

* comprimere JSON (anche semplicemente stringa minificata)
* oppure salvare “volumetrico pesante” in un file a parte (parquet/zstd) e in DB mettere solo `blob_ref`/path + hash. Ma questa è una fase 2.

---

## 5) Cose che ti conviene aggiungere subito (ma leggere)

### 5.1 Event log “raw” (opzionale ma utilissimo)

Quando fai ingest live, avere una tabella “append-only” degli eventi grezzi ti salva la vita.

```sql
CREATE TABLE ingest_events (
  id                 INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id             TEXT NOT NULL,
  event_type         TEXT NOT NULL,             -- 'ORDER'|'EXECUTION'|'BAR'|'RUN_STATUS'...
  event_utc          TEXT NOT NULL,
  payload_json       TEXT NOT NULL,
  received_utc       TEXT NOT NULL,
  FOREIGN KEY(run_id) REFERENCES strategy_runs(run_id)
);

CREATE INDEX idx_ingest_run_time ON ingest_events(run_id, event_utc);
```

Poi le tabelle normalizzate (orders/executions/bars) sono la “vista strutturata”.

### 5.2 Snapshot metriche e analisi

Hai già `metrics_json` su run, ma potresti aggiungere:

* `run_metrics_kv(run_id, key, value, unit)` se vuoi query rapide senza JSON.

---

## 6) Linee guida di ingest (per non incastrarti)

* **ID stabili**: usa `run_id` come UUID e tienilo uguale ovunque (come nel DTO) 
* **Upsert**: per orders/executions fai `INSERT ... ON CONFLICT(run_id, order_id) DO UPDATE ...`
* **FK “soft”**: evita vincoli che ti impediscono di salvare execution senza order già presente (per live succede)
* **Indici**: quelli sopra sono già quelli che impattano davvero (run/time, run/order_id, run/exec_time)

---

## 7) Mini-checklist: copre tutto ciò che hai chiesto?

* Correlazione **istanza ↔ run**: `strategy_instances.instance_id` → `strategy_runs.instance_id`
* Correlazione **run ↔ ordini ↔ eseguiti**: `orders.run_id`, `executions.run_id` + `order_id`
* Correlazioni interne **OCO**: `order_oco_groups` + `order_oco_links`
* Tracciamento **position impact type**: campo `position_impact` sia su `orders` che su `order_oco_links`
* Archiviazione **serie temporale** per run: `run_series` + `bars` (volumetrico esteso via JSON) 
* Pronto per endpoint FastAPI + SQLAlchemy: sì (schema chiaro, normalizzato)
