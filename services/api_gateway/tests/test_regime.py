from datetime import datetime, timedelta
from uuid import uuid4

from quant_shared.models.models import (
    RunSeries,
    RunSeriesRunLink,
    RunSeriesBar,
    Strategy,
    StrategyInstance,
    StrategyRun,
    Trade,
    Side,
    RunType
)

def _create_test_run(db_session, strategy_id=None, instance_id=None, run_id=None):
    strategy_id = strategy_id or f"test-regime-strategy-{uuid4()}"
    instance_id = instance_id or f"regime-instance-{uuid4()}"
    run_id = run_id or str(uuid4())

    strategy = Strategy(
        strategy_id=strategy_id,
        name="Regime Strategy",
        version="1.0",
        parameters_json=[]
    )
    db_session.add(strategy)

    instance = StrategyInstance(
        instance_id=instance_id,
        strategy_id=strategy.strategy_id,
        instance_name="Regime Instance",
        parameters_json=[],
        symbols_json=["TEST"],
        timeframe="1m"
    )
    db_session.add(instance)

    run = StrategyRun(
        run_id=run_id,
        instance_id=instance.instance_id,
        run_type=RunType.BACKTEST,
        start_utc=datetime.utcnow()
    )
    db_session.add(run)
    db_session.flush()
    return run.run_id

def _seed_trades(db_session, run_id, include_regime=True):
    base = datetime.utcnow()
    trades = [
        Trade(
            trade_id="regime-trade-1",
            run_id=run_id,
            symbol="TEST",
            side=Side.BUY,
            entry_time=base,
            exit_time=base + timedelta(minutes=1),
            entry_price=100,
            exit_price=120,
            quantity=1,
            pnl_net=20,
            regime_trend="BULL",
            regime_volatility="HIGH"
        ),
        Trade(
            trade_id="regime-trade-2",
            run_id=run_id,
            symbol="TEST",
            side=Side.BUY,
            entry_time=base + timedelta(minutes=2),
            exit_time=base + timedelta(minutes=3),
            entry_price=120,
            exit_price=115,
            quantity=1,
            pnl_net=-5,
            regime_trend="BULL",
            regime_volatility="LOW"
        ),
        Trade(
            trade_id="regime-trade-3",
            run_id=run_id,
            symbol="TEST",
            side=Side.SELL,
            entry_time=base + timedelta(minutes=4),
            exit_time=base + timedelta(minutes=5),
            entry_price=150,
            exit_price=135,
            quantity=1,
            pnl_net=15,
            regime_trend="BEAR" if include_regime else None,
            regime_volatility="NORMAL" if include_regime else None
        )
    ]
    db_session.add_all(trades)


def _seed_market_data(db_session, run_id, symbol="TEST", timeframe="1m", bar_count=520):
    series_id = f"regime-series-{run_id}"
    series = RunSeries(
        series_id=series_id,
        symbol=symbol,
        timeframe=timeframe,
        venue="TEST",
        provider="TEST"
    )
    db_session.add(series)
    db_session.flush()

    link = RunSeriesRunLink(
        series_id=series_id,
        run_id=run_id
    )
    db_session.add(link)

    base = datetime.utcnow()
    bars = []
    for i in range(bar_count):
        ts = base + timedelta(minutes=i)
        open_price = 100 + (i % 10) * 0.5
        close_price = open_price + ((i % 5) - 2) * 0.2
        high = max(open_price, close_price) + 0.1
        low = min(open_price, close_price) - 0.1
        bars.append(RunSeriesBar(
            series_id=series_id,
            ts_utc=ts,
            open=open_price,
            high=high,
            low=low,
            close=close_price,
            volume=100 + i
        ))

    db_session.add_all(bars)


def test_regime_router_returns_metrics(client, db_session):
    run_id = _create_test_run(db_session)
    _seed_trades(db_session, run_id)
    db_session.commit()

    response = client.get(f"/api/regime/{run_id}")
    assert response.status_code == 200

    payload = response.json()
    assert payload["run_id"] == run_id

    regime = payload.get("regime_performance", {})
    assert regime

    trend_map = {entry['name']: entry for entry in regime.get('trend', [])}
    assert trend_map['BULL']['pnl'] == 15.0
    assert trend_map['BULL']['count'] == 2
    assert trend_map['BULL']['profit_factor'] == 4.0

    vol_map = {entry['name']: entry for entry in regime.get('volatility', [])}
    assert vol_map['HIGH']['pnl'] == 20.0
    assert vol_map['LOW']['pnl'] == -5.0

    matrix = regime.get('matrix', {})
    assert matrix['BULL_HIGH']['pnl'] == 20.0
    assert matrix['BULL_LOW']['pnl'] == -5.0
    assert payload['tags_updated'] == 0


def test_regime_rebuild_endpoint(client, db_session):
    run_id = _create_test_run(db_session)
    _seed_trades(db_session, run_id, include_regime=False)
    _seed_market_data(db_session, run_id)
    db_session.commit()

    response = client.post(f"/api/regime/{run_id}/rebuild")
    assert response.status_code == 200

    payload = response.json()
    assert payload["run_id"] == run_id
    assert payload["trade_count"] == 3
    assert payload["regime_performance"] is not None
    assert payload["tags_updated"] > 0

    trades = db_session.query(Trade).filter(Trade.run_id == run_id).all()
    assert len(trades) == payload["trade_count"]
    assert all(t.regime_trend for t in trades)
    assert all(t.regime_volatility for t in trades)


def test_regime_rebuild_endpoint_no_trades(client, db_session):
    run_id = _create_test_run(db_session)
    db_session.commit()

    response = client.post(f"/api/regime/{run_id}/rebuild")
    assert response.status_code == 404
    assert response.json()["detail"] == "No trades to analyze"
