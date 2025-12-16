from sqlalchemy import (
    Column, String, Integer, Float, DateTime, ForeignKey, 
    Enum, JSON, Boolean, Text, UniqueConstraint, Index
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()

# --- Enums ---

class Side(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    MIT = "MIT" # Market if touched
    # Add others as needed

class OrderStatus(enum.Enum):
    NEW = "NEW"
    WORKING = "WORKING"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"

class PositionImpactType(enum.Enum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"
    REDUCE = "REDUCE"
    REVERSE = "REVERSE"
    UNKNOWN = "UNKNOWN"

class RunType(enum.Enum):
    BACKTEST = "BACKTEST"
    LIVE = "LIVE"
    PAPER = "PAPER"
    REPLAY = "REPLAY"

class RunStatus(enum.Enum):
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"

# --- Tables ---

class Strategy(Base):
    __tablename__ = 'strategies'

    strategy_id = Column(String, primary_key=True) # UUID
    name = Column(String, nullable=False)
    version = Column(String, nullable=True)
    vendor = Column(String, nullable=True) # Quantower / Custom
    source_ref = Column(String, nullable=True) # Repo URL / Commit
    created_utc = Column(DateTime, default=datetime.utcnow, nullable=False)
    notes = Column(Text, nullable=True)

    instances = relationship("StrategyInstance", back_populates="strategy")

class StrategyInstance(Base):
    __tablename__ = 'strategy_instances'

    instance_id = Column(String, primary_key=True) # UUID
    strategy_id = Column(String, ForeignKey('strategies.strategy_id'), nullable=False)
    
    instance_name = Column(String, nullable=True)
    parameters_json = Column(JSON, nullable=False)
    
    symbol = Column(String, nullable=True)
    symbols_json = Column(JSON, nullable=True) # Multi-symbol support
    
    timeframe = Column(String, nullable=True)
    account_id = Column(String, nullable=True)
    venue = Column(String, nullable=True)
    
    created_utc = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    strategy = relationship("Strategy", back_populates="instances")
    runs = relationship("StrategyRun", back_populates="instance")

class StrategyRun(Base):
    __tablename__ = 'strategy_runs'

    run_id = Column(String, primary_key=True) # UUID
    instance_id = Column(String, ForeignKey('strategy_instances.instance_id'), nullable=False)
    
    run_type = Column(Enum(RunType), nullable=False)
    
    start_utc = Column(DateTime, default=datetime.utcnow, nullable=False)
    end_utc = Column(DateTime, nullable=True)
    
    status = Column(Enum(RunStatus), default=RunStatus.RUNNING, nullable=False)
    
    engine_version = Column(String, nullable=True)
    data_source = Column(String, nullable=True)
    
    initial_balance = Column(Float, nullable=True)
    base_currency = Column(String, nullable=True)
    
    metrics_json = Column(JSON, nullable=True)
    created_utc = Column(DateTime, default=datetime.utcnow, nullable=False)

    instance = relationship("StrategyInstance", back_populates="runs")
    
    # Relationships
    orders = relationship("Order", back_populates="run")
    executions = relationship("Execution", back_populates="run")
    series_list = relationship("RunSeries", back_populates="run")
    events = relationship("IngestEvent", back_populates="run")
    oco_groups = relationship("OrderOcoGroup", back_populates="run")
    trades = relationship("Trade", back_populates="run")

    __table_args__ = (
        Index('idx_runs_instance_time', 'instance_id', 'start_utc'),
    )

class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('strategy_runs.run_id'), nullable=False)
    strategy_id = Column(String, nullable=True) # Optional redundancy
    
    order_id = Column(String, nullable=False) # Quantower ID
    parent_order_id = Column(String, nullable=True)
    
    symbol = Column(String, nullable=False)
    account_id = Column(String, nullable=True)
    
    side = Column(Enum(Side), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    time_in_force = Column(String, nullable=True)
    
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW, nullable=False)
    
    submit_utc = Column(DateTime, default=datetime.utcnow, nullable=False)
    update_utc = Column(DateTime, nullable=True)
    
    client_tag = Column(String, nullable=True)
    position_impact = Column(Enum(PositionImpactType), default=PositionImpactType.UNKNOWN, nullable=False)
    
    extra_json = Column(JSON, nullable=True)

    run = relationship("StrategyRun", back_populates="orders")
    
    __table_args__ = (
        UniqueConstraint('run_id', 'order_id', name='uq_run_order'),
        Index('idx_orders_run_time', 'run_id', 'submit_utc'),
        Index('idx_orders_symbol', 'symbol'),
    )

class Execution(Base):
    __tablename__ = 'executions'

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('strategy_runs.run_id'), nullable=False)
    
    execution_id = Column(String, nullable=False)
    order_id = Column(String, nullable=False)
    
    exec_utc = Column(DateTime, nullable=False)
    
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    
    fee = Column(Float, default=0.0)
    fee_currency = Column(String, nullable=True)
    liquidity = Column(String, nullable=True) # MAKER/TAKER
    position_impact = Column(Enum(PositionImpactType), default=PositionImpactType.UNKNOWN, nullable=True)
    
    extra_json = Column(JSON, nullable=True)

    run = relationship("StrategyRun", back_populates="executions")

    __table_args__ = (
        UniqueConstraint('run_id', 'execution_id', name='uq_run_execution'),
        Index('idx_exec_run_time', 'run_id', 'exec_utc'),
        Index('idx_exec_order', 'run_id', 'order_id'),
    )

class OrderOcoGroup(Base):
    __tablename__ = 'order_oco_groups'
    
    oco_group_id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey('strategy_runs.run_id'), nullable=False)
    created_utc = Column(DateTime, default=datetime.utcnow, nullable=False)
    label = Column(String, nullable=True)
    extra_json = Column(JSON, nullable=True)
    
    run = relationship("StrategyRun", back_populates="oco_groups")
    links = relationship("OrderOcoLink", back_populates="group")

class OrderOcoLink(Base):
    __tablename__ = 'order_oco_links'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('strategy_runs.run_id'), nullable=False)
    oco_group_id = Column(String, ForeignKey('order_oco_groups.oco_group_id'), nullable=False)
    order_id = Column(String, nullable=False) # Not FK to id, but logical link
    
    oco_role = Column(String, nullable=True) # TP/SL/ENTRY
    position_impact = Column(Enum(PositionImpactType), default=PositionImpactType.UNKNOWN)
    
    group = relationship("OrderOcoGroup", back_populates="links")
    
    __table_args__ = (
        UniqueConstraint('run_id', 'oco_group_id', 'order_id', name='uq_oco_link'),
        Index('idx_oco_links_order', 'run_id', 'order_id'),
    )

class RunSeries(Base):
    __tablename__ = 'run_series'
    
    series_id = Column(String, primary_key=True)
    run_id = Column(String, ForeignKey('strategy_runs.run_id'), nullable=False)
    
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    source = Column(String, nullable=True)
    
    start_utc = Column(DateTime, nullable=True)
    end_utc = Column(DateTime, nullable=True)
    
    has_volumetric = Column(Boolean, default=False)
    created_utc = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    run = relationship("StrategyRun", back_populates="series_list")
    bars = relationship("Bar", back_populates="series")

    __table_args__ = (
        UniqueConstraint('run_id', 'symbol', 'timeframe', name='uq_run_series'),
    )

class Bar(Base):
    __tablename__ = 'bars'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    series_id = Column(String, ForeignKey('run_series.series_id'), nullable=False)
    
    ts_utc = Column(DateTime, nullable=False)
    
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    
    volumetric_json = Column(JSON, nullable=True) # Bid/Ask vol, POC, etc.
    
    series = relationship("RunSeries", back_populates="bars")
    
    __table_args__ = (
        UniqueConstraint('series_id', 'ts_utc', name='uq_series_bar'),
        Index('idx_bars_series_time', 'series_id', 'ts_utc'),
    )

class IngestEvent(Base):
    __tablename__ = 'ingest_events'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(String, ForeignKey('strategy_runs.run_id'), nullable=False)
    
    event_type = Column(String, nullable=False)
    event_utc = Column(DateTime, nullable=False)
    
    payload_json = Column(JSON, nullable=False)
    received_utc = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    run = relationship("StrategyRun", back_populates="events")

    __table_args__ = (
        Index('idx_ingest_run_time', 'run_id', 'event_utc'),
    )

class MarketSeries(Base):
    __tablename__ = 'market_series'
    
    series_id = Column(String, primary_key=True) # Hash(symbol, timeframe, venue)
    
    symbol = Column(String, nullable=False)
    timeframe = Column(String, nullable=False)
    venue = Column(String, nullable=True) # e.g. Binance
    provider = Column(String, nullable=True) # e.g. Quantower
    
    created_utc = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    bars = relationship("MarketBar", back_populates="series")
    # Mapping to runs
    # runs = relationship("StrategyRun", secondary="run_subscriptions")

    __table_args__ = (
        UniqueConstraint('symbol', 'timeframe', 'venue', 'provider', name='uq_market_series_def'),
    )

class MarketBar(Base):
    __tablename__ = 'market_bars'
    
    series_id = Column(String, ForeignKey('market_series.series_id'), primary_key=True)
    ts_utc = Column(DateTime, primary_key=True)
    
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Float, default=0.0)
    
    volumetric_json = Column(JSON, nullable=True)
    
    series = relationship("MarketSeries", back_populates="bars")

class RunSubscription(Base):
    __tablename__ = 'run_subscriptions'
    
    run_id = Column(String, ForeignKey('strategy_runs.run_id'), primary_key=True)
    series_id = Column(String, ForeignKey('market_series.series_id'), primary_key=True)
    
    created_utc = Column(DateTime, default=datetime.utcnow)

class Trade(Base):
    __tablename__ = 'trades'

    trade_id = Column(String, primary_key=True) # UUID or similar
    run_id = Column(String, ForeignKey('strategy_runs.run_id'), nullable=False)
    
    symbol = Column(String, nullable=False)
    side = Column(Enum(Side), nullable=False) # LONG or SHORT
    
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=False)
    
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    
    quantity = Column(Float, nullable=False)
    
    pnl_net = Column(Float, nullable=False)
    pnl_gross = Column(Float, nullable=True)
    commission = Column(Float, default=0.0)
    
    # Advanced Metrics
    mae = Column(Float, nullable=True) # Maximum Adverse Excursion
    mfe = Column(Float, nullable=True) # Maximum Favorable Excursion
    
    duration_seconds = Column(Float, nullable=True)
    
    regime_trend = Column(String, nullable=True)
    regime_volatility = Column(String, nullable=True)
    
    extra_json = Column(JSON, nullable=True) # Custom strategy tags etc.

    run = relationship("StrategyRun", back_populates="trades")

    __table_args__ = (
        Index('idx_trades_run_time', 'run_id', 'exit_time'),
        Index('idx_trades_symbol', 'symbol'),
    )
