# 📅 Sprint 5 Plan: Quant Lab & Advanced Analytics

**Obiettivo Principale**: Trasformare la piattaforma da semplice strumento di reporting a laboratorio di ricerca quantitativa (Quant Lab).

## 1. Regime Detection (Market Classification)
Implementare algoritmi per classificare automaticamente le condizioni di mercato per ogni trade.
- **Backend (`src/quantlab/regime.py`)**:
    - Implementare indicatori di volatilità (ATR, Bollinger Bandwidth).
    - Implementare indicatori di trend (ADX, Moving Average Slope).
    - Funzione `detect_regime(bars)` che restituisce: `TRENDING_UP`, `TRENDING_DOWN`, `RANGING`, `HIGH_VOL`, `LOW_VOL`.
- **Database**:
    - Aggiungere colonne `regime_trend` e `regime_volatility` alla tabella `Trades` (o tabella correlata).
- **ETL**:
    - Calcolare e salvare il regime durante l'importazione o la ricostruzione dei trade.
- **Frontend**:
    - Visualizzare il regime nella tabella Trades e nei dettagli.
    - Filtrare le performance per regime (es. "Come performa la strategia in High Volatility?").

## 2. Parameter Lab & Tensor Visualization
Analisi multidimensionale dei parametri della strategia.
- **Backend**:
    - Endpoint per recuperare tutti i `StrategyRun` di una strategia raggruppati per parametri.
    - Struttura dati per "Grid Search Results": Mappa `{param1: v1, param2: v2} -> {net_profit, sharpe, ...}`.
- **Frontend (New Page: `/lab`)**:
    - **Parameter Selector**: UI per selezionare quali parametri variano (Assi X, Y, Z/Time).
    - **Heatmap 2D**: Visualizzazione classica (Param A vs Param B).
    - **Tensor Animator**:
        - Slider "Play" per scorrere attraverso una terza dimensione (es. Param C).
        - Il grafico (Heatmap o Surface 3D) si aggiorna in tempo reale mentre lo slider si muove, mostrando l'evoluzione della performance.
        - Esempio: Vedere come cambia la "Heatmap (StopLoss vs TakeProfit)" al variare del "Lookback Period".

## 3. Stress Testing (Monte Carlo)
Simulare scenari avversi.
- **Backend (`src/quantlab/stress.py`)**:
    - **Monte Carlo Shuffle**: Rimescolare l'ordine dei trade.
    - **Monte Carlo Noise**: Applicare variazioni casuali a Entry/Exit price (Slippage simulation).
    - **Equity Curve Simulation**: Generare N curve possibili.
- **Frontend**:
    - Visualizzare il "Cono di incertezza" (Confidence Intervals) attorno all'Equity Curve reale.
    - Metriche di rischio: VaR (Value at Risk), Probability of Ruin.

## 4. Setup Analysis (Pattern Tagging)
Collegare i trade a specifici pattern grafici.
- **Backend**:
    - Aggiungere campo `setup_tag` a `Trades`.
    - Endpoint per aggiornare il tag di un trade.
- **Frontend**:
    - UI nel dettaglio trade per selezionare/modificare il tag (es. "Breakout", "Reversal", "Pullback").
    - Report performance raggruppato per Setup.

---

## 📝 Ordine di Esecuzione Proposto

1.  **Regime Detection**: Fondamentale per contestualizzare i dati esistenti.
2.  **Parameter Lab (Tensor Viz)**: La feature "Wow" richiesta, richiede dati di più run (che possiamo simulare o importare).
3.  **Stress Testing**: Per validare la robustezza.
4.  **Setup Analysis**: Funzionalità più manuale/gestionale.
