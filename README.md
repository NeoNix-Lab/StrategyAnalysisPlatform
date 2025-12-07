# 🎯 Strategy Analysis Platform

Una piattaforma professionale per l'analisi quantitativa di strategie di trading, con ricostruzione automatica dei trade, calcolo di metriche avanzate (MAE/MFE) e dashboard interattive.

## ✨ Caratteristiche Principali

### 📊 Data Management
- **Importazione dati**: Supporto per barre OHLCV, ordini ed esecuzioni
- **Trade Reconstruction**: Algoritmo FIFO per ricostruire trade completi da fill parziali
- **Normalizzazione**: Gestione automatica di timezone, simboli e duplicati

### 📈 Analytics Avanzate
- **Metriche per Trade**: MAE (Maximum Adverse Excursion), MFE (Maximum Favorable Excursion), durata, PnL
- **Metriche di Portafoglio**: Win Rate, Profit Factor, Max Drawdown, Equity Curve
- **Regime Detection**: Classificazione automatica trend/range e volatilità
- **Monte Carlo**: Stress testing con simulazioni di shuffle dei trade

### 🖥️ Dashboard Interattiva
- **KPI Cards**: Visualizzazione immediata delle metriche chiave
- **Equity Curve**: Grafico interattivo dell'andamento del capitale
- **Scatter Plot MAE/MFE**: Analisi visiva dell'efficienza dei trade
- **Istogramma PnL**: Distribuzione dei profitti/perdite
- **Trade Inspector**: Click su un trade per vedere il grafico a candele con marker di entry/exit

## 🚀 Quick Start

### Prerequisiti
- Python 3.10+
- Node.js 18+ (per il frontend)

### Installazione

1. **Clona il repository** (o estrai i file)

2. **Installa le dipendenze Python**:
```powershell
pip install -r requirements.txt
```

3. **Installa le dipendenze Frontend**:
```powershell
cd frontend
npm install
cd ..
```

4. **Genera dati di esempio**:
```powershell
python seed_data.py
```

### Avvio Rapido

#### Opzione 1: Script Automatico (Consigliato)
Doppio click su `START.bat` per avviare automaticamente backend e frontend.

#### Opzione 2: Manuale
**Terminale 1 - Backend**:
```powershell
python run_server.py
```

**Terminale 2 - Frontend**:
```powershell
cd frontend
npm run dev
```

Poi apri il browser su: **http://localhost:5173**

## 📁 Struttura del Progetto

```
StrategyAnalysisPlatform/
├── src/
│   ├── api/              # FastAPI backend
│   │   ├── main.py       # Entry point API
│   │   └── routers/      # Endpoint organizzati
│   ├── core/             # Logica di business
│   │   ├── trade_builder.py  # Ricostruzione trade
│   │   └── analytics.py      # Calcolo metriche
│   ├── database/         # Modelli e connessione DB
│   ├── etl/              # Import dati
│   └── quantlab/         # Analisi avanzate
│       ├── regime.py     # Regime detection
│       └── stress_test.py # Monte Carlo
├── frontend/             # React + Vite
│   └── src/
│       ├── App.jsx       # Dashboard principale
│       └── components/   # Componenti riutilizzabili
├── data/                 # Dati importati (gitignored)
├── trading_data.db       # Database SQLite
├── seed_data.py          # Script per dati di test
├── run_server.py         # Avvio backend
├── START.bat             # Launcher automatico
└── ROADMAP.md            # Piano di sviluppo

```

## 🛠️ Stack Tecnologico

### Backend
- **FastAPI**: API REST ad alte prestazioni
- **SQLAlchemy**: ORM per gestione database
- **Pandas/NumPy**: Analisi dati e calcoli numerici
- **SQLite**: Database locale (facilmente sostituibile con PostgreSQL)

### Frontend
- **React 18**: Libreria UI moderna
- **Vite**: Build tool velocissimo
- **Recharts**: Grafici statistici
- **Lightweight Charts**: Grafici a candele professionali (TradingView)
- **Axios**: Client HTTP

## 📖 Utilizzo

### Importare i Tuoi Dati

1. **Prepara i file CSV** con le colonne richieste (vedi `src/etl/importer.py`)
2. **Modifica lo script di import** o usa l'API
3. **Esegui la ricostruzione dei trade**:
```python
from src.core.trade_builder import TradeBuilder
from src.database.connection import SessionLocal

db = SessionLocal()
builder = TradeBuilder(db)
trades = builder.reconstruct_trades("TUA_STRATEGIA", "SIMBOLO")
```

### API Endpoints

- `GET /api/trades/` - Lista trade con filtri
- `GET /api/trades/stats?strategy_id=X` - Statistiche aggregate
- `GET /api/bars/` - Dati storici (OHLCV)
- `GET /docs` - Documentazione interattiva (Swagger)

## 🎨 Personalizzazione

### Tema
Modifica le variabili CSS in `frontend/src/App.css`:
```css
:root {
  --bg-color: #0f172a;
  --accent: #38bdf8;
  /* ... */
}
```

### Metriche Custom
Aggiungi nuove metriche in `src/core/analytics.py` e aggiornala dashboard.

## 📝 Roadmap

Vedi `ROADMAP.md` per il piano di sviluppo completo.

## 🤝 Contributi

Questo è un progetto personale, ma suggerimenti e feedback sono benvenuti!

## 📄 Licenza

Uso personale.

---

**Creato con ❤️ per trader quantitativi**
