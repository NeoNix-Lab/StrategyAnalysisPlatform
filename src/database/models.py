from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, Enum, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
import enum

Base = declarative_base()

class Side(enum.Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(enum.Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    # Add others as needed

class OrderStatus(enum.Enum):
    NEW = "NEW"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    FILLED = "FILLED"
    CANCELED = "CANCELED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class Strategy(Base):
    __tablename__ = 'strategies'
    
    strategy_id = Column(String, primary_key=True) # e.g. "StackedImbalance"
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    default_parameters = Column(JSON, nullable=True)
    
    runs = relationship("StrategyRun", back_populates="strategy")

class StrategyRun(Base):
    __tablename__ = 'strategy_runs'
    
    run_id = Column(String, primary_key=True) # UUID
    strategy_id = Column(String, ForeignKey('strategies.strategy_id'), nullable=False)
    
    parameters = Column(JSON, nullable=True)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime, nullable=True)
    status = Column(String, default="RUNNING") # RUNNING, COMPLETED, FAILED
    data_range = Column(JSON, nullable=True) # {symbol, start, end, timeframe}
    
    strategy = relationship("Strategy", back_populates="runs")
    trades = relationship("Trade", back_populates="run")
    orders = relationship("Order", back_populates="run")

class Bar(Base):
    __tablename__ = 'bars'

    # Composite primary key logic or just a surrogate ID? 
    # Usually Symbol + Timeframe + Timestamp is unique.
    # For simplicity/performance in SQLite, we might use a surrogate ID or just rely on the index.
    # Let's use a composite PK for data integrity.
    
    symbol = Column(String, primary_key=True)
    timeframe = Column(String, primary_key=True)
    timestamp = Column(DateTime, primary_key=True) # Start time
    
    end_time = Column(DateTime)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
    open_interest = Column(Float, nullable=True)

    def __repr__(self):
        return f"<Bar(symbol={self.symbol}, time={self.timestamp}, close={self.close})>"

class Order(Base):
    __tablename__ = 'orders'

    order_id = Column(String, primary_key=True)
    parent_order_id = Column(String, nullable=True)
    
    # Link to Run instead of just Strategy ID
    run_id = Column(String, ForeignKey('strategy_runs.run_id'), nullable=True) # Nullable for migration
    strategy_id = Column(String, nullable=False) # Keep for denormalization/legacy
    
    strategy_version = Column(String, nullable=True)
    account_id = Column(String, nullable=False)
    symbol = Column(String, nullable=False)
    
    side = Column(Enum(Side), nullable=False)
    order_type = Column(Enum(OrderType), nullable=False)
    time_in_force = Column(String, default="GTC")
    
    submit_time = Column(DateTime, default=datetime.utcnow)
    
    price = Column(Float, nullable=True)
    stop_price = Column(Float, nullable=True)
    quantity = Column(Float, nullable=False)
    
    status = Column(Enum(OrderStatus), default=OrderStatus.NEW)
    reject_reason = Column(String, nullable=True)
    cancel_reason = Column(String, nullable=True)
    
    client_tag = Column(String, nullable=True)
    meta_json = Column(JSON, nullable=True)

    # Relationships
    executions = relationship("Execution", back_populates="order")
    run = relationship("StrategyRun", back_populates="orders")

    def __repr__(self):
        return f"<Order(id={self.order_id}, symbol={self.symbol}, side={self.side}, status={self.status})>"

class Execution(Base):
    __tablename__ = 'executions'

    execution_id = Column(String, primary_key=True)
    order_id = Column(String, ForeignKey('orders.order_id'), nullable=False)
    
    strategy_id = Column(String, nullable=True) # Redundant but useful for fast queries if needed, or join order
    account_id = Column(String, nullable=True)
    symbol = Column(String, nullable=False)
    
    side = Column(Enum(Side), nullable=False)
    exec_time = Column(DateTime, default=datetime.utcnow)
    
    price = Column(Float, nullable=False)
    quantity = Column(Float, nullable=False)
    
    fee = Column(Float, default=0.0)
    fee_currency = Column(String, nullable=True)
    liquidity_flag = Column(String, nullable=True)

    # Relationships
    order = relationship("Order", back_populates="executions")

    def __repr__(self):
        return f"<Execution(id={self.execution_id}, order={self.order_id}, price={self.price}, qty={self.quantity})>"

class Trade(Base):
    __tablename__ = 'trades'

    trade_id = Column(String, primary_key=True)
    
    # Link to Run
    run_id = Column(String, ForeignKey('strategy_runs.run_id'), nullable=True) # Nullable for migration
    strategy_id = Column(String, nullable=False)
    
    symbol = Column(String, nullable=False)
    
    side = Column(Enum(Side), nullable=False) # LONG or SHORT
    
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime, nullable=False)
    
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float, nullable=False)
    
    quantity = Column(Float, nullable=False)
    
    pnl_gross = Column(Float, nullable=False)
    pnl_net = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    
    # Metriche avanzate (popolate successivamente)
    mae = Column(Float, nullable=True)
    mfe = Column(Float, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    # Regime Analysis
    regime_trend = Column(String, nullable=True) # BULL, BEAR, RANGE
    regime_volatility = Column(String, nullable=True) # HIGH, LOW, NORMAL
    
    # Setup/Pattern Tagging
    setup_tag = Column(String, nullable=True) # es. "Breakout", "Pullback", "Reversal"

    run = relationship("StrategyRun", back_populates="trades")

    def __repr__(self):
        return f"<Trade(id={self.trade_id}, symbol={self.symbol}, pnl={self.pnl_net})>"

class Experiment(Base):
    __tablename__ = 'experiments'
    
    experiment_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Parametri base o configurazione fissa
    base_config = Column(JSON, nullable=True)
    
    runs = relationship("ExperimentRun", back_populates="experiment")

class ExperimentRun(Base):
    __tablename__ = 'experiment_runs'
    
    run_id = Column(String, primary_key=True)
    experiment_id = Column(String, ForeignKey('experiments.experiment_id'), nullable=False)
    
    parameters = Column(JSON, nullable=False) # I parametri specifici di questo run
    
    # Risultati
    metrics = Column(JSON, nullable=True) # Win rate, profit factor, etc.
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    experiment = relationship("Experiment", back_populates="runs")
