from sqlalchemy.orm import Session
from sqlalchemy import func
from src.database.models import Trade, Bar, Side
import pandas as pd
import numpy as np

class TradeAnalyzer:
    def __init__(self, db_session: Session):
        self.db = db_session

    def calculate_mae_mfe(self, trade_id: str):
        """
        Calcola MAE e MFE per un singolo trade basandosi sui dati delle barre.
        """
        trade = self.db.query(Trade).filter(Trade.trade_id == trade_id).first()
        if not trade:
            return

        # Recupera le barre che coprono la durata del trade
        # Nota: Questo assume che abbiamo barre a timeframe sufficientemente basso (es. 1m)
        # per una stima accurata.
        bars = self.db.query(Bar).filter(
            Bar.symbol == trade.symbol,
            Bar.timestamp >= trade.entry_time,
            Bar.timestamp <= trade.exit_time
        ).all()

        if not bars:
            print(f"⚠️ Nessuna barra trovata per il trade {trade_id} ({trade.symbol}). Impossibile calcolare MAE/MFE.")
            return

        # Estrai Highs e Lows
        highs = [b.high for b in bars]
        lows = [b.low for b in bars]
        
        max_price = max(highs)
        min_price = min(lows)

        if trade.side == Side.BUY:
            # LONG: MFE è la distanza verso l'alto (High), MAE verso il basso (Low)
            mfe = max_price - trade.entry_price
            mae = trade.entry_price - min_price
        else:
            # SHORT: MFE è la distanza verso il basso (Low), MAE verso l'alto (High)
            mfe = trade.entry_price - min_price
            mae = max_price - trade.entry_price

        # Aggiorna il trade
        trade.mae = max(0.0, mae) # MAE è sempre >= 0 (distanza avversa)
        trade.mfe = max(0.0, mfe) # MFE è sempre >= 0 (distanza favorevole)
        
        self.db.commit()

    def calculate_portfolio_metrics(self, strategy_id: str, run_id: str = None):
        """
        Calcola metriche aggregate per una strategia.
        Restituisce un dizionario.
        """
        query = self.db.query(Trade).filter(Trade.strategy_id == strategy_id)
        if run_id:
            query = query.filter(Trade.run_id == run_id)
            
        trades = query.all()
        if not trades:
            return {
                "total_trades": 0,
                "win_rate": 0,
                "profit_factor": 0,
                "average_trade": 0,
                "max_drawdown": 0,
                "net_profit": 0
            }

        # Convert trades to dict, handling enums
        trade_dicts = []
        for t in trades:
            d = t.__dict__.copy()
            # Remove SQLAlchemy internal state
            d.pop('_sa_instance_state', None)
            # Convert enum to string
            if 'side' in d and hasattr(d['side'], 'name'):
                d['side'] = d['side'].name
            trade_dicts.append(d)
        
        df = pd.DataFrame(trade_dicts)

        total_trades = len(df)
        winning_trades = df[df['pnl_net'] > 0]
        losing_trades = df[df['pnl_net'] <= 0]

        win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0
        
        gross_profit = winning_trades['pnl_net'].sum()
        gross_loss = abs(losing_trades['pnl_net'].sum())
        
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        avg_trade = df['pnl_net'].mean()
        
        # Drawdown calculation (Equity Curve)
        df = df.sort_values('exit_time')
        df['cumulative_pnl'] = df['pnl_net'].cumsum()
        df['peak'] = df['cumulative_pnl'].cummax()
        df['drawdown'] = df['cumulative_pnl'] - df['peak']
        max_drawdown = df['drawdown'].min()

        return {
            "total_trades": total_trades,
            "win_rate": round(win_rate * 100, 2),
            "profit_factor": round(profit_factor, 2),
            "average_trade": round(avg_trade, 2),
            "max_drawdown": round(max_drawdown, 2),
            "net_profit": round(df['cumulative_pnl'].iloc[-1], 2)
        }
