
import pytest
from unittest.mock import MagicMock
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
from src.services.analytics.standard_analyzer import StandardAnalyzer
from src.database.models import Trade, Execution

# Mock structures equivalent to database models
class MockTrade:
    def __init__(self, pnl_net, exit_time, side='BUY', entry_price=100.0, exit_price=105.0, quantity=1.0, commission=0.0, mae=0.0, mfe=0.0):
        self.pnl_net = pnl_net
        self.exit_time = exit_time
        self.side = MagicMock()
        self.side.name = side
        self.entry_price = entry_price
        self.exit_price = exit_price
        self.quantity = quantity
        self.commission = commission
        self.mae = mae
        self.mfe = mfe
        self.run_id = "test_run"
        self.strategy_id = "test_strategy"

class MockExecution:
    def __init__(self, fee=0.0, price=100.0, quantity=1.0, order_id="ord1", exec_utc=None):
        self.fee = fee
        self.price = price
        self.quantity = quantity
        self.order_id = order_id
        self.run_id = "test_run"
        self.exec_utc = exec_utc or datetime.utcnow()


@pytest.fixture
def mock_db_session():
    return MagicMock()

@pytest.fixture
def analyzer(mock_db_session):
    return StandardAnalyzer(mock_db_session)

@pytest.fixture
def setup_query_mock(mock_db_session):
    def _setup(trades=None, executions=None):
        trades = trades or []
        executions = executions or []
        
        def query_side_effect(model):
            mock = MagicMock()
            mock.join.return_value = mock
            mock.filter.return_value = mock
            
            if model == Trade:
                mock.all.return_value = trades
            elif model == Execution:
                mock.all.return_value = executions
            else:
                mock.all.return_value = []
            return mock
            
        mock_db_session.query.side_effect = query_side_effect
    return _setup

def test_calculate_metrics_basic(analyzer, setup_query_mock):
    # Setup mock trades
    trades = [
        MockTrade(pnl_net=100, exit_time=datetime(2023, 1, 1)),
        MockTrade(pnl_net=-50, exit_time=datetime(2023, 1, 2)),
        MockTrade(pnl_net=200, exit_time=datetime(2023, 1, 3))
    ]
    
    setup_query_mock(trades=trades, executions=[])
    
    metrics = analyzer.calculate_portfolio_metrics(strategy_id="test_strat", run_id="test_run")
    
    assert metrics['total_trades'] == 3
    assert metrics['net_profit'] == 250.0
    assert metrics['win_rate'] == 66.67
    assert metrics['profit_factor'] == 6.0

def test_calculate_fees_and_slippage(analyzer, setup_query_mock):
    trades = [MockTrade(pnl_net=90, exit_time=datetime(2023, 1, 1))]
    executions = [MockExecution(fee=2.5), MockExecution(fee=2.5)]
    
    setup_query_mock(trades=trades, executions=executions)
    
    metrics = analyzer.calculate_portfolio_metrics(strategy_id="test_strat", run_id="test_run")
    assert metrics.get('total_fees') == 5.0

def test_equity_curve_generation(analyzer, setup_query_mock):
    trades = [
        MockTrade(pnl_net=10, exit_time=datetime(2023, 1, 1, 10, 0)),
        MockTrade(pnl_net=20, exit_time=datetime(2023, 1, 1, 11, 0)),
        MockTrade(pnl_net=-5, exit_time=datetime(2023, 1, 1, 12, 0))
    ]
    setup_query_mock(trades=trades, executions=[])
    
    metrics = analyzer.calculate_portfolio_metrics(strategy_id="test_strat", run_id="test_run")
    curve = metrics.get('equity_curve', [])
    assert len(curve) == 3

def test_stability_metric(analyzer, setup_query_mock):
    # Perfectly linear equity curve: 10, 10, 10, 10
    trades = [
        MockTrade(pnl_net=10, exit_time=datetime(2023, 1, 1)),
        MockTrade(pnl_net=10, exit_time=datetime(2023, 1, 2)),
        MockTrade(pnl_net=10, exit_time=datetime(2023, 1, 3)),
        MockTrade(pnl_net=10, exit_time=datetime(2023, 1, 4)),
    ]
    setup_query_mock(trades=trades, executions=[])
    
    metrics = analyzer.calculate_portfolio_metrics(strategy_id="test_strat", run_id="test_run")
    
    # R2 should be 1.0 for a perfect line
    assert metrics.get('stability_r2') == 1.0
    
    # Volatile curve
    trades_volatile = [
        MockTrade(pnl_net=100, exit_time=datetime(2023, 1, 1)),
        MockTrade(pnl_net=-90, exit_time=datetime(2023, 1, 2)),
        MockTrade(pnl_net=100, exit_time=datetime(2023, 1, 3)),
    ]
    setup_query_mock(trades=trades_volatile, executions=[])
    metrics_v = analyzer.calculate_portfolio_metrics(strategy_id="test_strat", run_id="test_run_v")
    
    # R2 should be low
    assert metrics_v.get('stability_r2') < 0.9

    # Check Skewness/Kurtosis existence
    # We have 3 trades: 100, -90, 100. Distribution: [100, -90, 100]
    # Skew should be negative (tail on left due to -90)
    assert metrics_v.get('pnl_skew') is not None
    # 3 points might be too few for reliable skew calculation in some libs, but pandas handles it (n-1/n-2)
    # Our implementation checks for len < 5 and returns 0.0
    # So for 3 trades, it should return 0.0
    assert metrics_v.get('pnl_skew') == 0.0
    
    # Let's test with 5 trades to trigger calculation
    trades_5 = [
        MockTrade(pnl_net=10, exit_time=datetime(2023, 1, 1)),
        MockTrade(pnl_net=10, exit_time=datetime(2023, 1, 2)),
        MockTrade(pnl_net=10, exit_time=datetime(2023, 1, 3)),
        MockTrade(pnl_net=10, exit_time=datetime(2023, 1, 4)),
        MockTrade(pnl_net=-50, exit_time=datetime(2023, 1, 5)) # Outlier negative
    ]
    setup_query_mock(trades=trades_5, executions=[])
    metrics_5 = analyzer.calculate_portfolio_metrics(strategy_id="test_strat", run_id="test_run_5")
    # Skew should be negative
    assert metrics_5.get('pnl_skew') < 0

def test_sharpe_annualization(analyzer):
    trades = [
        MockTrade(pnl_net=100, exit_time=datetime(2023, 1, 1)),
        MockTrade(pnl_net=100, exit_time=datetime(2023, 1, 2)),
        MockTrade(pnl_net=100, exit_time=datetime(2023, 1, 3)),
        MockTrade(pnl_net=-100, exit_time=datetime(2023, 1, 4)), # Loss
        MockTrade(pnl_net=50, exit_time=datetime(2023, 1, 5)),
    ]
    trade_dicts = [t.__dict__ for t in trades]
    df = pd.DataFrame(trade_dicts)
    sharpe = analyzer._calculate_sharpe(df['pnl_net'], annualized=True)
    raw_sharpe = analyzer._calculate_sharpe(df['pnl_net'], annualized=False)
    assert sharpe > raw_sharpe
