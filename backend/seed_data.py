import random
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.database.connection import SessionLocal, init_db
from src.database.models import Bar, Order, Execution, Side, OrderType, OrderStatus
from src.core.trade_builder import TradeBuilder
    # from src.core.analytics import TradeAnalyzer (DEPRECATED)
import uuid

def generate_sine_wave_data(start_date, num_bars=1000):
    """Genera dati OHLCV sintetici basati su una sinusoide con rumore."""
    dates = [start_date + timedelta(minutes=i) for i in range(num_bars)]
    base_price = 100.0
    
    # Trend + Sinusoide + Rumore
    t = np.linspace(0, 4*np.pi, num_bars)
    trend = np.linspace(0, 10, num_bars)
    noise = np.random.normal(0, 0.5, num_bars)
    
    prices = base_price + 10 * np.sin(t) + trend + noise
    
    bars = []
    for i, p in enumerate(prices):
        # Crea candele realistiche attorno al prezzo base
        open_p = p
        close_p = p + np.random.normal(0, 0.2)
        high_p = max(open_p, close_p) + abs(np.random.normal(0, 0.1))
        low_p = min(open_p, close_p) - abs(np.random.normal(0, 0.1))
        
        bars.append(Bar(
            symbol="DEMO_TICKER",
            timeframe="1m",
            timestamp=dates[i],
            open=round(open_p, 2),
            high=round(high_p, 2),
            low=round(low_p, 2),
            close=round(close_p, 2),
            volume=int(abs(np.random.normal(100, 20)))
        ))
    return bars

def generate_trades(db, bars):
    """Simula una strategia semplice (random entry) sui dati generati."""
    orders = []
    executions = []
    
    strategy_id = "DEMO_STRAT"
    account_id = "ACC_001"
    symbol = "DEMO_TICKER"
    
    position = 0 # 0, 1 (Long), -1 (Short)
    entry_price = 0
    
    for i in range(20, len(bars), 50): # Ogni 50 barre prova a fare qualcosa
        bar = bars[i]
        
        # Se siamo flat, entriamo
        if position == 0:
            side = Side.BUY if random.random() > 0.5 else Side.SELL
            qty = 1.0
            
            order_id = str(uuid.uuid4())
            order = Order(
                order_id=order_id,
                strategy_id=strategy_id,
                account_id=account_id,
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=qty,
                status=OrderStatus.FILLED,
                submit_time=bar.timestamp,
                price=bar.close
            )
            orders.append(order)
            
            exec_id = str(uuid.uuid4())
            execution = Execution(
                execution_id=exec_id,
                order_id=order_id,
                strategy_id=strategy_id,
                account_id=account_id,
                symbol=symbol,
                side=side,
                exec_time=bar.timestamp,
                price=bar.close,
                quantity=qty,
                fee=0.5 # 0.5€ commission
            )
            executions.append(execution)
            
            position = 1 if side == Side.BUY else -1
            entry_price = bar.close
            
        # Se siamo a mercato, chiudiamo (random o stop/tp simulato)
        elif position != 0:
            # Chiudiamo
            side = Side.SELL if position == 1 else Side.BUY
            qty = 1.0
            
            order_id = str(uuid.uuid4())
            order = Order(
                order_id=order_id,
                strategy_id=strategy_id,
                account_id=account_id,
                symbol=symbol,
                side=side,
                order_type=OrderType.MARKET,
                quantity=qty,
                status=OrderStatus.FILLED,
                submit_time=bar.timestamp,
                price=bar.close
            )
            orders.append(order)
            
            exec_id = str(uuid.uuid4())
            execution = Execution(
                execution_id=exec_id,
                order_id=order_id,
                strategy_id=strategy_id,
                account_id=account_id,
                symbol=symbol,
                side=side,
                exec_time=bar.timestamp,
                price=bar.close,
                quantity=qty,
                fee=0.5
            )
            executions.append(execution)
            
            position = 0

    # Salva tutto
    db.bulk_save_objects(orders)
    db.bulk_save_objects(executions)
    db.commit()
    print(f"Generati {len(orders)} ordini e {len(executions)} esecuzioni.")

def main():
    init_db()
    db = SessionLocal()
    
    print("Generazione dati barre...")
    bars = generate_sine_wave_data(datetime.utcnow() - timedelta(days=2))
    db.bulk_save_objects(bars)
    db.commit()
    print(f"Salvate {len(bars)} barre.")
    
    print("Generazione trading simulato...")
    generate_trades(db, bars)
    
    print("Ricostruzione Trade...")
    builder = TradeBuilder(db)
    trades = builder.reconstruct_trades("DEMO_STRAT", "DEMO_TICKER")
    
    print("Calcolo Metriche Avanzate (MAE/MFE) con Analytics Service...")
    from src.services.analytics import AnalyticsRouter
    analyzer = AnalyticsRouter(db)
    for t in trades:
        analyzer.calculate_trade_metrics(t.trade_id)
    
    print("✅ Seed completato! Ora puoi avviare la dashboard.")
    db.close()

if __name__ == "__main__":
    main()
