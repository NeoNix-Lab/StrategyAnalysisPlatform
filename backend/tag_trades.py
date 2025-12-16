from sqlalchemy.orm import Session
from src.database.connection import SessionLocal, engine
from src.database.models import Trade, MarketBar, MarketSeries, StrategyRun, StrategyInstance, Side, RunSeries, Bar
from src.quantlab.regime import RegimeDetector
import pandas as pd
from sqlalchemy import text
from datetime import timedelta
import sys

def tag_trades():
    db = SessionLocal()
    
    print("Starting trade tagging (MAE/MFE + Regime) using MARKET DATA...")
    
    runs = db.query(StrategyRun).all()
    print(f"Found {len(runs)} strategy runs.")
    
    total_updated = 0
    
    # Pre-fetch all Market Series to minimize queries
    market_series_map = {} # (symbol, timeframe) -> series_id
    all_m_series = db.query(MarketSeries).all()
    for ms in all_m_series:
        market_series_map[(ms.symbol, ms.timeframe)] = ms.series_id
        # Also handle potential default venue/provider mismatches if strict matching fails
        # But let's assume strict for now
        
    print(f"Available Market Series: {list(market_series_map.keys())}")
    
    for run in runs:
        print(f"Processing Run: {run.run_id}")
        
        # Get Instance Info
        instance = db.query(StrategyInstance).filter(StrategyInstance.instance_id == run.instance_id).first()
        if not instance:
            print(f"  Missing instance for run {run.run_id}. Skipping.")
            continue
            
        symbol = instance.symbol
        timeframe = instance.timeframe
        
        # Fallback if instance doesn't have them (e.g. from parameters)
        if not symbol or not timeframe:
             # Try to guess from orders or trades?
             # For now, skip
             print("  No symbol/timeframe in instance. Skipping.")
             continue
             
        # Look for Market Series
        m_series_id = market_series_map.get((symbol, timeframe))
        
        if not m_series_id:
            print(f"  No MarketSeries found for {symbol} {timeframe}. Checking generic...")
            # Fuzzy match? Or maybe user only has 1 series
            if len(market_series_map) == 1:
                 m_series_id = list(market_series_map.values())[0]
                 print(f"  Using default series: {m_series_id}")
            else:
                 continue
                 
        # Load Bars
        bars_query = db.query(MarketBar).filter(MarketBar.series_id == m_series_id).order_by(MarketBar.ts_utc.asc())
        df_bars = pd.read_sql(bars_query.statement, db.bind)
        
        if df_bars.empty:
            print(f"  No bars data for market series {m_series_id}. Skipping.")
            continue
            
        if 'ts_utc' in df_bars.columns:
            df_bars['ts_utc'] = pd.to_datetime(df_bars['ts_utc'])
            
        # 5. Calculate Regime
        df_regime = RegimeDetector.calculate_regime(df_bars)
        if not df_regime.empty and 'ts_utc' in df_regime.columns:
            df_regime = df_regime.sort_values('ts_utc')
            
        # 6. Load Trades
        trades = db.query(Trade).filter(Trade.run_id == run.run_id).all()
        print(f"  Found {len(trades)} trades for run.")
        
        run_updated = 0
        for trade in trades:
            # Check if already tagged to clear old data? Or just overwrite.
            
            # --- A. MAE / MFE Calculation ---
            trade_bars = df_bars[
                (df_bars['ts_utc'] >= trade.entry_time) & 
                (df_bars['ts_utc'] <= trade.exit_time)
            ]
            
            if not trade_bars.empty:
                highs = trade_bars['high'].max()
                lows = trade_bars['low'].min()
                
                if trade.side == Side.BUY:
                    mfe = highs - trade.entry_price
                    mae = trade.entry_price - lows
                else: # SELL
                    mfe = trade.entry_price - lows
                    mae = highs - trade.entry_price
                    
                trade.mae = max(0.0, mae)
                trade.mfe = max(0.0, mfe)
                
            # --- B. Regime Tagging ---
            if not df_regime.empty and 'ts_utc' in df_regime.columns:
                try:
                    idx = df_regime['ts_utc'].searchsorted(trade.entry_time, side='right') - 1
                    if idx >= 0:
                        regime_row = df_regime.iloc[idx]
                        trade.regime_trend = regime_row['regime_trend']
                        trade.regime_volatility = regime_row['regime_volatility']
                except Exception:
                    pass
            
            run_updated += 1
            
        total_updated += run_updated
        db.commit()
        print(f"  Updated {run_updated} trades.")
    
    print(f"✅ Processed {total_updated} trades total.")
    db.close()

if __name__ == "__main__":
    tag_trades()
