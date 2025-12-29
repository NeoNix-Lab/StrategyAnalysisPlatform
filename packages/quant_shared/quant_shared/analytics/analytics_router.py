from sqlalchemy.orm import Session
from .standard_analyzer import StandardAnalyzer

class AnalyticsRouter:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.handlers = {
            'DEFAULT': StandardAnalyzer(db_session),
            # 'SCALPING': HighFreqAnalyzer(db_session), # Future ext
            # 'SWING': PortfolioAnalyzer(db_session)    # Future ext
        }

    def route_analysis(self, strategy_id: str = None, run_id: str = None, strategy_type: str = 'DEFAULT'):
        """
        Routes the analysis request to the appropriate analyzer based on strategy type.
        Returns the calculated metrics dictionary.
        """
        handler = self.handlers.get(strategy_type, self.handlers['DEFAULT'])
        
        # 1. Calculate Portfolio/Run level metrics
        metrics = handler.calculate_portfolio_metrics(strategy_id=strategy_id, run_id=run_id)
        
        # 2. (Optional) Trigger trade-level analysis (MAE/MFE)
        # We might want to do this asynchronously or on-demand
        # For now, we can iterate trades and update them if needed, 
        # but let's keep it lightweight. 
        # handler.calculate_mae_mfe(trade_id) <-- loop trades?
        
        return metrics

    def calculate_trade_metrics(self, trade_id: str, strategy_type: str = 'DEFAULT'):
        """
        Calculates specific metrics for a single trade (e.g. MAE/MFE).
        """
        handler = self.handlers.get(strategy_type, self.handlers['DEFAULT'])
        handler.calculate_mae_mfe(trade_id)
