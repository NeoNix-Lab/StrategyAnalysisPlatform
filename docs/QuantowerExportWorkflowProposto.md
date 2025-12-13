Di seguito ti elenco **cosa esportare** (campi minimi + consigliati) da Quantower, **evento per evento**, mappandolo alla tua struttura DB (strategies / strategy_instances / strategy_runs / orders / executions / OCO / run_series / bars / ingest_events).

> Regola generale: per ogni evento, esporta sempre anche un “header” comune: `run_id`, `instance_id`, `strategy_id`, `event_utc`, `event_type`, `payload_version`, `source` (live/backtest), `sequence` (contatore monotono). Ti semplifica debug e replay.

---

## 1) OnStrategyCreate

Obiettivo: creare/aggiornare **strategy** e **strategy_instance**.

**Esporta:**

* **Strategy**

  * `strategy_id` (UUID tuo)
  * `name`, `version`
  * `vendor/source_ref` (se riesci: package, assembly, commit, path DLL)
* **Instance**

  * `instance_id` (UUID tuo)
  * `strategy_id`
  * `instance_name`
  * `parameters_json` (snapshot completo parametri)
  * `symbol` oppure `symbols_json` (multi-symbol)
  * `timeframe`
  * `account_id`, `venue` (se disponibili)
  * `created_utc`

**DB target:** `strategies`, `strategy_instances`, (opzionale) `ingest_events`.

---

## 2) OnStrategyRun

Obiettivo: aprire una **strategy_run** e fissare il contesto di esecuzione.

**Esporta:**

* `run_id` (UUID tuo, coerente con i DTO che già usi)
* `instance_id`
* `run_type` (`BACKTEST|LIVE|PAPER|REPLAY`)
* `start_utc`
* `engine_version` (Quantower version + exporter version)
* `data_source` (provider, storico, cache, ecc.)
* `initial_balance`, `base_currency` (se accessibili)
* `status = RUNNING`

**DB target:** `strategy_runs`, `ingest_events`.

---

## 3) OrderAdded

Obiettivo: inserire/upsert su **orders**, e se puoi già collegare OCO/ruolo/impact.

**Esporta (minimo):**

* `order_id` (Quantower)
* `run_id`
* `symbol`, `account_id`
* `side` (BUY/SELL)
* `order_type` (MARKET/LIMIT/STOP/…)
* `tif`
* `quantity`
* `price`, `stop_price` (se applicabili)
* `status` iniziale (NEW/WORKING/…)
* `submit_utc` (timestamp ordine)
* `client_tag` / `comment` (se lo imposti dalla strategy)
* `parent_order_id` (se bracket/child)

**Esporta (consigliato per analisi):**

* `request_id` / `client_order_id` (se esiste)
* `reduce_only`, `post_only` (se derivati/crypto)
* `sl_tp_flags` (se riesci a dedurre che è TP/SL)
* `position_impact` (vedi nota sotto)

**OCO (se disponibile):**

* `oco_group_id` (se Quantower espone un id; altrimenti lo generi tu)
* `oco_role` (TP/SL/ENTRY/EXIT)
* `position_impact` specifico del leg

**DB target:** `orders`, `order_oco_groups`, `order_oco_links`, `ingest_events`.

**Nota PositionImpactType:**
Se Quantower non te lo fornisce “diretto”, lo calcoli lato exporter con logica deterministica (es. confronto con posizione corrente al momento dell’invio/accettazione ordine). Anche una stima “UNKNOWN→poi aggiorno” va bene.

---

## 4) OrderRemoved

Obiettivo: aggiornare stato e motivazione su **orders**.

**Esporta:**

* `order_id`, `run_id`
* `status` finale (CANCELED/REJECTED/EXPIRED/FILLED)
* `update_utc`
* `reason` (stringa/enum se disponibile)
* `last_known_qty` e `filled_qty` (se esposti; utile)

**DB target:** `orders` (upsert/update), `ingest_events`.

---

## 5) NewHistoryItem

Obiettivo: “history” in Quantower spesso include **order/trade/position events**. Nella tua struttura, conviene usarlo come **event log** e come fonte per normalizzare se gli altri eventi mancano (specialmente in backtest).

**Esporta:**

* `history_item_id` (se esiste)
* `item_type` (ORDER_EVENT / TRADE / POSITION / MESSAGE / FILL…)
* `event_utc`
* `payload_json` completo (raw)
* eventuali chiavi:

  * `order_id`
  * `execution_id` / `trade_id`
  * `position_id`
  * `symbol`

**DB target:** `ingest_events` (forte), + upsert su tabelle core se ti serve.

---

## 6) HistoryItemUpdated

Obiettivo: aggiornare qualcosa già arrivato (stato ordine, trade aggiornato, posizione aggiornata).

**Esporta:**

* `history_item_id`
* `event_utc`
* `diff_json` (o payload completo aggiornato)
* le chiavi di correlazione (`order_id`, `execution_id`, `position_id`)

**DB target:** `ingest_events`, + update su `orders/executions/positions` (se presenti).

---

## 7) TradeAdded

Nel tuo DB “trade” può essere:

* o **execution/fill** (più comune)
* o “trade” aggregato (open→close). Dipende dall’oggetto Quantower.

**Se TradeAdded = fill (consigliato trattarlo come execution):**
Esporta:

* `execution_id` (o `trade_id` ma univoco)
* `order_id`
* `run_id`
* `exec_utc`
* `price`, `quantity`
* `fee`, `fee_currency`
* `liquidity` (maker/taker se c’è)
* `extra_json` (raw)

**DB target:** `executions`, `ingest_events`.

**Se TradeAdded = trade aggregato (round-trip):**
Allora aggiungeresti una tabella `trades` dedicata. Ma finché non sei sicuro, salva raw + mappa a executions se possibile.

---

## 8) TradeRemoved

**Esporta:**

* `execution_id/trade_id`, `run_id`
* `update_utc`
* `reason`

**DB target:** `executions` (o `trades`), `ingest_events`.

---

## 9) PositionAdded

Nel tuo schema attuale non ho incluso `positions`. Per quello che vuoi fare (impact, exposure, equity), conviene aggiungerla.

**Consiglio:** aggiungi tabella:

* `positions(run_id, position_id, symbol, side, qty, avg_price, open_utc, close_utc, status, unrealized_pnl, realized_pnl, extra_json)`

**Esporta:**

* `position_id` (Quantower)
* `symbol`, `account_id`
* `side` (LONG/SHORT)
* `quantity`, `avg_price`
* `open_utc`
* `status`

**DB target:** `positions` (nuova) + `ingest_events`.

---

## 10) PositionRemoved

**Esporta:**

* `position_id`, `run_id`
* `close_utc`
* `realized_pnl` (se disponibile)
* `status = CLOSED`
* eventuale motivo (liquidation/manual/strategy)

**DB target:** `positions`, `ingest_events`.

---

## 11) OnStop

Obiettivo: chiusura run (anche se la strategy non viene rimossa).

**Esporta:**

* `run_id`
* `end_utc`
* `status` (COMPLETED/CANCELED/FAILED)
* `metrics_json` (aggregati finali: pnl, dd, trades count, winrate, ecc. se li calcoli)
* `error` (se fallita)
* `series_snapshot_info` (se hai esportato bars)

**DB target:** `strategy_runs` (update), `ingest_events`.

---

## 12) OnStrategyRemoved

Obiettivo: lifecycle dell’istanza (non per forza della run).

**Esporta:**

* `instance_id`
* `removed_utc`
* `reason` (manual unload, chart closed, ecc.)

**DB target:** opzionale `strategy_instances` (campo `removed_utc`) + `ingest_events`.

---

# Extra: esportazione serie temporale (quando e cosa)

Non è legata a un singolo evento, ma puoi agganciarla a:

* `OnStrategyRun` (snapshot iniziale)
* oppure al primo accesso dati della strategy
* oppure “solo se non presente”: calcoli hash e decidi

**Esporta (per run_series/bars):**

* `symbol`, `timeframe`, `source`
* per ogni bar: `ts_utc, o,h,l,c, volume`
* se volumetrico: `volumetric_json` (delta, bid/ask, poc, imbalances, ecc.)

---

# In pratica: set minimo che ti rende “robusto”

Se dovessi scegliere i più importanti per partire senza buchi:

* OnStrategyCreate
* OnStrategyRun
* OrderAdded / OrderRemoved
* TradeAdded (o NewHistoryItem se Trade non è affidabile)
* OnStop

PositionAdded/Removed li aggiungi appena vuoi calcolare bene `position_impact` e analisi exposure.
