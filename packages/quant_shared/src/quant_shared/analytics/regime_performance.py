import pandas as pd


class RegimePerformanceAggregator:
    REGIME_TRENDS = ['BULL', 'BEAR', 'RANGE']
    REGIME_VOLS = ['HIGH', 'NORMAL', 'LOW']

    @classmethod
    def aggregate(cls, df: pd.DataFrame) -> dict:
        if df is None or df.empty or 'pnl_net' not in df.columns:
            return cls.empty()

        has_trend = 'regime_trend' in df.columns
        has_vol = 'regime_volatility' in df.columns

        trend_stats = []
        for trend in cls.REGIME_TRENDS:
            subset = df[df['regime_trend'] == trend] if has_trend else pd.DataFrame()
            entry = cls._summarize(subset)
            entry["name"] = trend
            trend_stats.append(entry)

        vol_stats = []
        for vol in cls.REGIME_VOLS:
            subset = df[df['regime_volatility'] == vol] if has_vol else pd.DataFrame()
            entry = cls._summarize(subset)
            entry["name"] = vol
            vol_stats.append(entry)

        matrix = {}
        for trend in cls.REGIME_TRENDS:
            for vol in cls.REGIME_VOLS:
                if has_trend and has_vol:
                    subset = df[(df['regime_trend'] == trend) & (df['regime_volatility'] == vol)]
                elif has_trend:
                    subset = df[df['regime_trend'] == trend]
                elif has_vol:
                    subset = df[df['regime_volatility'] == vol]
                else:
                    subset = pd.DataFrame()
                entry = cls._summarize(subset)
                entry["trend"] = trend
                entry["volatility"] = vol
                matrix[f"{trend}_{vol}"] = entry

        return {
            "trend": trend_stats,
            "volatility": vol_stats,
            "matrix": matrix
        }

    @classmethod
    def empty(cls) -> dict:
        return {
            "trend": [
                {"name": trend, **cls._empty_entry()}
                for trend in cls.REGIME_TRENDS
            ],
            "volatility": [
                {"name": vol, **cls._empty_entry()}
                for vol in cls.REGIME_VOLS
            ],
            "matrix": {
                f"{trend}_{vol}": {"trend": trend, "volatility": vol, **cls._empty_entry()}
                for trend in cls.REGIME_TRENDS
                for vol in cls.REGIME_VOLS
            }
        }

    @classmethod
    def _summarize(cls, subset: pd.DataFrame) -> dict:
        if subset is None or subset.empty or 'pnl_net' not in subset.columns:
            return cls._empty_entry()

        valid = subset[subset['pnl_net'].notna()]
        if valid.empty:
            return cls._empty_entry()

        total = len(valid)
        pnl_sum = valid['pnl_net'].sum()
        wins = valid[valid['pnl_net'] > 0]
        losses = valid[valid['pnl_net'] <= 0]
        win_rate = (len(wins) / total) * 100 if total else 0.0
        gross_profit = wins['pnl_net'].sum()
        gross_loss = abs(losses['pnl_net'].sum())
        pf = cls._profit_factor(gross_profit, gross_loss)

        return {
            "pnl": round(pnl_sum, 2),
            "count": int(total),
            "win_rate": round(win_rate, 2),
            "profit_factor": round(pf, 2) if pf is not None else None
        }

    @staticmethod
    def _profit_factor(gross_profit: float, gross_loss: float):
        if gross_loss > 0:
            return gross_profit / gross_loss
        if gross_profit == 0:
            return 0.0
        return None

    @staticmethod
    def _empty_entry() -> dict:
        return {
            "pnl": 0.0,
            "count": 0,
            "win_rate": 0.0,
            "profit_factor": 0.0
        }
