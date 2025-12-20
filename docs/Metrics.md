Di seguito trovi una **lista strutturata di metriche per la valutazione di strategie di trading algoritmico**, organizzata **per livello di maturità**, dalla base fino a metriche quantitative avanzate.
La selezione è pensata per essere **coerente con una piattaforma tipo Quantower + backend analitico**, come quella che stai progettando.

---

## 1. Metriche di base (P&L e trade-level)

Fondamentali, immediate, servono per capire *se* la strategia funziona.

**Performance**

* Net Profit / Net P&L
* Gross Profit / Gross Loss
* Return (%)
* Average Trade P&L
* Profit per Trade
* Profit per Day / Run

**Trade statistics**

* Number of Trades
* Winning Trades / Losing Trades
* Win Rate (%)
* Loss Rate (%)
* Average Win
* Average Loss
* Max Win / Max Loss

**Costi**

* Total Fees
* Fees per Trade
* Slippage (medio / max)

---

## 2. Metriche di rischio classiche

Misurano *quanto* stai rischiando per ottenere il risultato.

**Drawdown**

* Max Drawdown (assoluto e %)
* Average Drawdown
* Drawdown Duration
* Time to Recovery

**Volatilità**

* Equity Volatility
* P&L Standard Deviation

**Rapporti rischio/rendimento**

* Risk/Reward Ratio
* Expectancy
* Profit Factor

---

## 3. Metriche risk-adjusted (standard quantitative)

Qui inizi a confrontare strategie in modo serio.

* Sharpe Ratio
* Sortino Ratio
* Calmar Ratio
* MAR Ratio
* Omega Ratio

*(Nota: queste metriche diventano molto più affidabili se calcolate per run omogenee e timeframe coerenti)*

---

## 4. Metriche di stabilità e robustezza

Servono a capire *quanto è fragile* la strategia.

**Equity behavior**

* Equity Curve Smoothness
* Equity Linearity (R²)
* Ulcer Index

**Trade distribution**

* Skewness del P&L
* Kurtosis del P&L
* Trade P&L Variance

**Temporal stability**

* Monthly / Weekly Consistency
* % Periodi Profittevoli
* Rolling Sharpe / Rolling P&L

---

## 5. Metriche di execution & micro-struttura

Molto rilevanti in ambienti volumetrici / HFT-like.

* Fill Ratio
* Partial Fill Rate
* Order-to-Fill Latency
* Slippage vs Expected Price
* Price Improvement (%)
* Rejected / Canceled Orders Ratio

---

## 6. Metriche di posizione e rischio operativo

Fondamentali per strategie multi-ordine, OCO, scaling.

* Max Position Size
* Average Exposure
* Time in Market (%)
* Max Concurrent Positions
* Leverage Utilization
* Margin Usage

---

## 7. Metriche avanzate di portafoglio / run-correlation

Qui entri in ambito *platform-level*.

* Correlation between Strategy Runs
* Correlation with Benchmark
* Correlation between Symbols
* Diversification Ratio
* Contribution to Portfolio Risk
* Marginal Sharpe per Strategia

---

## 8. Metriche di comportamento strategico

Utilissime per ML, clustering e comparazione avanzata.

* Trade Frequency Profile
* Holding Time Distribution
* Entry Efficiency
* Exit Efficiency
* MAE / MFE (Maximum Adverse / Favorable Excursion)
* Capture Ratio (trend / range)

---

## 9. Metriche probabilistiche e stress

Livello avanzato, ideale per validazione finale.

* Value at Risk (VaR)
* Conditional VaR (CVaR)
* Monte Carlo Drawdown Distribution
* Probability of Ruin
* Tail Risk
* Worst-Case Scenario P&L

---

## 10. Metriche “ML-ready” (feature di confronto)

Pensate per ranking, clustering, auto-selection.

* Strategy Score (composito pesato)
* Normalized Performance Vector
* Distance from Efficient Frontier
* Dominance Ratio
* Regime Sensitivity Index

---

### Nota architetturale (importante per te)

Con la struttura dati che stai progettando:

* **Run → Orders → Executions → Positions**
* **Time series opzionali per run**

puoi calcolare **oltre il 90% di queste metriche in modo deterministico**, e le rimanenti con **aggregazioni rolling o batch**.

Se vuoi, nel prossimo step posso:

* suggerirti **quali metriche calcolare live vs batch**
* definire un **core set minimo (10–15 metriche)** per ranking automatico
* proporti una **schema table “metrics” versionata per run** pronta per FastAPI + frontend.
