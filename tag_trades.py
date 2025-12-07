from sqlalchemy.orm import Session
from src.database.connection import SessionLocal, engine
from src.database.models import Trade, Bar, Base
from src.quantlab.regime import RegimeDetector
import pandas as pd
import sys

from sqlalchemy import text

def tag_trades():
    db = SessionLocal()
    
    # 1. Aggiorna schema DB (aggiunge colonne se mancano)
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE trades ADD COLUMN regime_trend VARCHAR"))
            conn.execute(text("ALTER TABLE trades ADD COLUMN regime_volatility VARCHAR"))
            conn.commit() # Importante per SQLAlchemy 2.0+
            print("Colonne regime aggiunte.")
    except Exception as e:
        print(f"Colonne probabilmente già esistenti o errore non critico: {e}")

    print("Inizio tagging dei trade...")
    
    # 2. Carica Dati Barre
    # Assumiamo un solo simbolo per ora: DEMO_TICKER
    symbol = "DEMO_TICKER"
    bars_query = db.query(Bar).filter(Bar.symbol == symbol).order_by(Bar.timestamp.asc())
    df_bars = pd.read_sql(bars_query.statement, db.bind)
    
    if df_bars.empty:
        print("Nessuna barra trovata!")
        return

    print(f"Caricate {len(df_bars)} barre.")

    # 3. Calcola Regime
    df_regime = RegimeDetector.calculate_regime(df_bars)
    # Indicizza per timestamp per lookup veloce
    df_regime.set_index('timestamp', inplace=True)
    
    # 4. Carica Trade
    trades = db.query(Trade).filter(Trade.symbol == symbol).all()
    print(f"Trovati {len(trades)} trade da analizzare.")
    
    updated_count = 0
    for trade in trades:
        # Trova il regime all'entry time
        # Usiamo 'asof' per trovare la barra più vicina (o esatta)
        try:
            # Cerca l'indice (timestamp) più vicino all'entry_time del trade
            idx = df_regime.index.get_indexer([trade.entry_time], method='nearest')[0]
            regime_data = df_regime.iloc[idx]
            
            trade.regime_trend = regime_data['regime_trend']
            trade.regime_volatility = regime_data['regime_volatility']
            updated_count += 1
        except Exception as e:
            print(f"Errore tagging trade {trade.trade_id}: {e}")
            
    db.commit()
    print(f"✅ Aggiornati {updated_count} trade con successo.")
    db.close()

if __name__ == "__main__":
    tag_trades()
