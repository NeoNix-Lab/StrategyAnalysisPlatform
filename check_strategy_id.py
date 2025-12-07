from src.database.connection import engine
from sqlalchemy.orm import Session
from src.database.models import Trade

with Session(engine) as db:
    # Get unique strategy IDs
    trades = db.query(Trade).all()
    strategy_ids = set(t.strategy_id for t in trades)
    
    print("Strategy IDs nel database:")
    for sid in strategy_ids:
        count = db.query(Trade).filter(Trade.strategy_id == sid).count()
        print(f"  - '{sid}': {count} trade")
    
    if trades:
        print(f"\nPrimo trade completo:")
        t = trades[0]
        print(f"  strategy_id: {t.strategy_id}")
        print(f"  symbol: {t.symbol}")
        print(f"  side: {t.side}")
