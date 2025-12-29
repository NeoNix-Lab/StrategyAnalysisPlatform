from metrics import MetricsEngine
from datetime import datetime, timedelta

def test_metrics():
    print("Testing MetricsEngine...")
    
    # Mock Executions
    class MockExecution:
        def __init__(self, eid, oid, price, qty, time):
            self.execution_id = eid
            self.order_id = oid
            self.price = price
            self.quantity = qty
            self.exec_utc = time

    class MockOrder:
        def __init__(self, oid, side, symbol):
            self.order_id = oid
            self.side = side
            self.symbol = symbol

    t0 = datetime(2023, 1, 1, 10, 0, 0)
    
    # Scenario: 
    # Order 1: Buy 1 @ 100
    # Order 2: Sell 1 @ 110 (Win 10)
    # Order 3: Buy 1 @ 100
    # Order 4: Sell 1 @ 90 (Loss 10)
    
    orders = [
        MockOrder("O1", "BUY", "BTC"),
        MockOrder("O2", "SELL", "BTC"),
        MockOrder("O3", "BUY", "BTC"),
        MockOrder("O4", "SELL", "BTC"),
    ]
    
    executions = [
        MockExecution("E1", "O1", 100.0, 1.0, t0),
        MockExecution("E2", "O2", 110.0, 1.0, t0 + timedelta(minutes=5)),
        MockExecution("E3", "O3", 100.0, 1.0, t0 + timedelta(minutes=10)),
        MockExecution("E4", "O4", 90.0, 1.0, t0 + timedelta(minutes=15)),
    ]
    
    reconstructed = MetricsEngine.reconstruct_trades(executions, orders)
    print(f"Reconstructed Trades: {len(reconstructed)}")
    for t in reconstructed:
        print(f"Trade: {t['side']} {t['entry_price']} -> {t['exit_price']} PnL: {t['pnl_net']}")
        
    metrics = MetricsEngine.calculate_trade_metrics(reconstructed)
    print("Metrics:", metrics)
    
    assert metrics['total_trades'] == 2
    assert metrics['winning_trades'] == 1
    assert metrics['losing_trades'] == 1
    assert metrics['net_profit'] == 0.0
    assert metrics['gross_profit'] == 10.0
    assert metrics['gross_loss'] == -10.0

    print("SUCCESS: Metrics are correct.")

if __name__ == "__main__":
    test_metrics()
