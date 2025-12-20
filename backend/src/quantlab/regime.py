import pandas as pd
import numpy as np

class RegimeDetector:
    @staticmethod
    def calculate_regime(df: pd.DataFrame, period: int = 20) -> pd.DataFrame:
        """
        Calcola il regime di mercato (Trend e Volatilità) per ogni barra.
        Richiede un DataFrame con colonne: open, high, low, close.
        Assumes 'ts_utc' as the timestamp column.
        """
        if df.empty:
            return pd.DataFrame(columns=['ts_utc', 'regime_trend', 'regime_volatility'])
            
        df = df.copy()
        
        # Ensure we have a sorted index or column for rolling ops
        if 'ts_utc' in df.columns:
            df.sort_values('ts_utc', inplace=True)
        
        # --- 1. Trend Detection (SMA + ADX proxy) ---
        # Usiamo una combinazione di SMA per determinare il trend
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # Calcolo pendenza SMA 50 (proxy per forza trend)
        df['sma_50_slope'] = df['sma_50'].diff(periods=5)
        
        conditions_trend = [
            (df['close'] > df['sma_50']) & (df['sma_50'] > df['sma_200']), # Strong Bull
            (df['close'] < df['sma_50']) & (df['sma_50'] < df['sma_200']), # Strong Bear
        ]
        choices_trend = ['BULL', 'BEAR']
        df['regime_trend'] = np.select(conditions_trend, choices_trend, default='RANGE')
        
        # --- 2. Volatility Detection (Bollinger Band Width) ---
        # BB Width = (Upper - Lower) / Middle
        df['std_dev'] = df['close'].rolling(window=period).std()
        
        # Ricalcoliamo BB standard su sma_20
        sma_20 = df['close'].rolling(window=20).mean()
        std_20 = df['close'].rolling(window=20).std()
        
        # Avoid division by zero
        sma_20 = sma_20.replace(0, np.nan)
        
        df['bb_width'] = (4 * std_20) / sma_20 # (Upper - Lower) / Middle approx
        
        # Percentili dinamici per definire High/Low volatility
        # Usiamo una finestra mobile per i percentili per adattarci al regime recente
        lookback_vol = 500
        df['vol_p80'] = df['bb_width'].rolling(window=lookback_vol).quantile(0.8)
        df['vol_p20'] = df['bb_width'].rolling(window=lookback_vol).quantile(0.2)
        
        conditions_vol = [
            (df['bb_width'] > df['vol_p80']),
            (df['bb_width'] < df['vol_p20'])
        ]
        choices_vol = ['HIGH', 'LOW']
        df['regime_volatility'] = np.select(conditions_vol, choices_vol, default='NORMAL')
        
        columns_to_return = ['regime_trend', 'regime_volatility']
        if 'ts_utc' in df.columns:
            columns_to_return.insert(0, 'ts_utc')
            
        return df[columns_to_return]
