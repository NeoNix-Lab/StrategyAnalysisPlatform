from sqlalchemy.orm import Session
from src.database.connection import SessionLocal
from src.database.models import Trade

def inspect_trades_regime():
    db = SessionLocal()
    
    # Get a sample of trades that have regime data
    trades = db.query(Trade).filter(Trade.regime_trend.isnot(None)).limit(10).all()
    
    print(f"Trades with regime data (first 10 found):")
    for t in trades:
        print(f"ID: {t.trade_id} | Trend: '{t.regime_trend}' | Vol: '{t.regime_volatility}' | PnL: {t.pnl_net}")
        
    # Check count of NULLs
    null_count = db.query(Trade).filter(Trade.regime_trend.is_(None)).count()
    total_count = db.query(Trade).count()
    
    print(f"\nTotal Trades: {total_count}")
    print(f"Trades with NULL regime: {null_count}")
    
    db.close()

if __name__ == "__main__":
    inspect_trades_regime()
