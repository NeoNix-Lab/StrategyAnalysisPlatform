# Data Management Optimization: Robust Bar & Series Handling

## 1. Objective
To implement a robust data ingestion pipeline that guarantees:
- **Zero Duplicates**: Idempotent storage execution for Market Data (Bars).
- **Temporal Consistency**: Accurate tracking of UTC time ranges to identify and manage data gaps.
- **Provider Integrity**: Strict validation of Data Source (Venue/Provider) to ensure symbol consistency.
- **Efficiency**: Minimize redundant storage when multiple strategies run on the same instrument.

## 2. Gap Analysis (Current System)
Currently, `RunSeries` is tightly coupled to `StrategyRun`.
- **Identity**: `(run_id, symbol, timeframe)`
- **Issue**: If 5 strategies run on `BTC/USDT`, we store 5 identical copies of the market data.
- **Issue**: If a disconnection occurs, we just resume. We lack explicit "Gap" markers in the database to warn the analyst.

## 3. Proposed Architecture: "Unified Market Data Layer"

### 3.1. Decoupling Series from Runs
Instead of `RunSeries` belonging to a `Run`, we propose a **Shared Market Data Model**:

#### New Entity: `MarketSeries`
Unique Key: `(Symbol, Timeframe, Provider, Venue)`
- **Symbol**: Normalized ticker (e.g., `BTC/USDT`).
- **Timeframe**: Standardized string (e.g., `1-Min`).
- **Provider**: The data source app (e.g., `Quantower`).
- **Venue**: The exchange (e.g., `Binance`).
- **Coverage**: `start_utc` - `end_utc`.

#### Relation: `RunSubscription`
Links a `StrategyRun` to a `MarketSeries`.
- Allows multiple runs to reference the *same* underlying price data.
- Saves massive storage space.

### 3.2. Deduplication & Upsert Logic
**Algorithm**:
1. **Receipt**: Receive `Bar` packet from Exporter.
2. **Identification**: Hash `(Symbol, Timeframe, Venue)` to find target `MarketSeries`.
3. **Idempotency**:
   - Query DB for existing Bar at `ts_utc`.
   - **If Exists**: Update/Overwrite (handles corrections).
   - **If New**: Insert.
4. **Optimization**:
   - Use Batch Inserts (bulk flush every 1s or 100 bars) for high throughput.
   - Use SQL Upsert (`INSERT ... ON CONFLICT DO UPDATE`) instead of `Select` + `Insert`.

### 3.3. Time Range & Continuity Control
To ensure data quality for backtesting:

1. **Continuous Check**:
   - Keep a memory cache of `last_bar_time` for active series.
   - If `new_bar_time` > `last_bar_time + timeframe_interval`:
     - **Flag GAP**: Log a `DataGap` event.
     - Auto-trigger a "History Request" to fill the gap (if supported by Exporter).

2. **Session Boundaries**:
   - Track `connection_status` provided by the Exporter.
   - Explicitly mark periods where the Strategy was "Offline" vs "No Market Activity".

### 3.4. Connection & Symbol Safety
**Problem**: `BTCUSD` (Binance) != `BTC/USD` (Coinbase) in price and volume.
**Solution**:
- **Strict Strictness**: A Series is unique to its `Venue`.
- **Normalization**: Middleware maps incoming synonyms to a canonical Symbol ID (e.g., `BTC-USDT` -> `BTC/USDT`).

## 4. Implementation Steps (Roadmap)
1. **Schema Migration**:
   - Create `market_series` and `market_bars` tables.
   - Migrate `RunSeries` to be a mapping table.
2. **Backend Update (`ingest.py`)**:
   - Modify `on_bar` to write to the shared `market_bars` table.
   - Implement `ON CONFLICT` logic.
3. **Exporter Update (C#)**:
   - Send `Provider` and `Venue` metadata in `BarDTO`.
   - Send `ConnectionStatus` events.

## 5. Benefits
- **Storage**: Reduces DB size by factor of N (N = concurrent strategies).
- **Analytics**: Enables cross-strategy correlation analysis on the exact same dataset.
- **Reliability**: Explicit gap detection ensures "What you see is what you backtest".
