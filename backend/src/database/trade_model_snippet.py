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
    
    extra_json = Column(JSON, nullable=True) # Custom strategy tags etc.

    run = relationship("StrategyRun", back_populates="trades")

    __table_args__ = (
        Index('idx_trades_run_time', 'run_id', 'exit_time'),
        Index('idx_trades_symbol', 'symbol'),
    )
