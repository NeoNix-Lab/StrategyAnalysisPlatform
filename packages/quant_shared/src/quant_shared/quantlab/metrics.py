from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

#TODO: utilizzare questo approccio in modo discrezionale via ui (potrebbe essere utile per valutare le performance temporanee di strategie di headging)
# ma l approccio de siderato sarebbe quello di inserire i trade collegati alle esecuzioni via ingest ed eventualmente utilizzare sistemi di rigenerazione dei dati
# mancanti se e solo se necessario 

class MetricsEngine:
    @staticmethod
    def reconstruct_trades(executions: List[Any], orders: List[Any]) -> List[Dict[str, Any]]:
        """
        Reconstructs trades from executions/orders.
        """
        # 1. Map Orders by ID for quick lookup
        orders_map = {o.order_id: o for o in orders}
        
        # 2. Reconstruct Trades (Simplified: 1 Round Trip = Trade)
        trades = []
        
        # Temporary tracking
        open_positions = {} 
        
        # sort executions
        sorted_execs = sorted(executions, key=lambda x: x.exec_utc)
        
        completed_trades = []
        
        for exc in sorted_execs:
            order = orders_map.get(exc.order_id)
            if not order:
                continue
                
            side = order.side.name if hasattr(order.side, 'name') else str(order.side)
            symbol = order.symbol
            
            # FIFO Stack
            if symbol not in open_positions:
                open_positions[symbol] = []
                
            stack = open_positions[symbol]
            
            remaining_qty = exc.quantity
            
            # While we have something in stack and sides are opposite
            while remaining_qty > 0 and stack:
                top = stack[0] # FIFO
                
                # Check for opposite side
                is_opposite = (side == 'BUY' and top['side'] == 'SELL') or (side == 'SELL' and top['side'] == 'BUY')
                
                if is_opposite:
                    matched_qty = min(remaining_qty, top['quantity'])
                    
                    entry_price = top['price']
                    exit_price = exc.price
                    
                    direction = 1 if top['side'] == 'BUY' else -1
                    pnl = (exit_price - entry_price) * matched_qty * direction
                    
                    completed_trades.append({
                        "trade_id": f"{top['order_id']}_{exc.execution_id}", # Synthetic ID
                        "symbol": symbol,
                        "side": top['side'], 
                        "entry_time": top['time'],
                        "exit_time": exc.exec_utc,
                        "entry_price": entry_price,
                        "exit_price": exit_price,
                        "pnl_net": pnl,
                        "pnl_gross": pnl,
                        "quantity": matched_qty,
                        "duration_seconds": (exc.exec_utc - top['time']).total_seconds()
                    })
                    
                    remaining_qty -= matched_qty
                    top['quantity'] -= matched_qty
                    
                    if top['quantity'] <= 0.0000001:
                        stack.pop(0) # Remove filled
                else:
                    break
                    
            if remaining_qty > 0.0000001:
                stack.append({
                    "order_id": exc.order_id,
                    "price": exc.price,
                    "quantity": remaining_qty,
                    "side": side,
                    "time": exc.exec_utc
                })
        
        return completed_trades

    @staticmethod
    def reconstruct_and_calculate(executions: List[Any], orders: List[Any]) -> Dict[str, Any]:
        trades = MetricsEngine.reconstruct_trades(executions, orders)
        return MetricsEngine.calculate_trade_metrics(trades)

    @staticmethod
    def calculate_trade_metrics(trades: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculates core metrics from a list of trade dictionaries.
        Expected keys in trade dicts: 'pnl_net', 'pnl_gross', 'side', 'duration_seconds' (optional).
        """
        if not trades:
            return MetricsEngine._empty_metrics()

        df = pd.DataFrame(trades)
        
        # Ensure necessary columns exist
        if 'pnl_net' not in df.columns:
            return MetricsEngine._empty_metrics()
            
        # Basic Counts
        total_trades = len(df)
        winning_trades = df[df['pnl_net'] > 0]
        losing_trades = df[df['pnl_net'] <= 0]
        n_winners = len(winning_trades)
        n_losers = len(losing_trades)

        # Performance
        net_profit = df['pnl_net'].sum()
        gross_profit = winning_trades['pnl_net'].sum() if not winning_trades.empty else 0.0
        gross_loss = losing_trades['pnl_net'].sum() if not losing_trades.empty else 0.0
        
        avg_trade = df['pnl_net'].mean()
        avg_win = winning_trades['pnl_net'].mean() if not winning_trades.empty else 0.0
        avg_loss = losing_trades['pnl_net'].mean() if not losing_trades.empty else 0.0
        
        largest_win = df['pnl_net'].max()
        largest_loss = df['pnl_net'].min()

        # Ratios
        win_rate = (n_winners / total_trades) * 100 if total_trades > 0 else 0.0
        profit_factor = abs(gross_profit / gross_loss) if gross_loss != 0 else (999.0 if gross_profit > 0 else 0.0)

        # Streak Analysis (Simplified)
        # TODO: Implement max consecutive wins/losses

        # Return Dict
        return {
            "total_trades": int(total_trades),
            "winning_trades": int(n_winners),
            "losing_trades": int(n_losers),
            "win_rate": round(win_rate, 2),
            "net_profit": round(net_profit, 2),
            "gross_profit": round(gross_profit, 2),
            "gross_loss": round(gross_loss, 2),
            "profit_factor": round(profit_factor, 2),
            "average_trade": round(avg_trade, 2),
            "average_win": round(avg_win, 2),
            "average_loss": round(avg_loss, 2),
            "largest_win": round(largest_win, 2),
            "largest_loss": round(largest_loss, 2),
            "max_drawdown": 0.0, # Placeholder, needs equity curve
            "sharpe_ratio": 0.0, # Placeholder
            "sortino_ratio": 0.0  # Placeholder
        }

    @staticmethod
    def _empty_metrics() -> Dict[str, Any]:
        return {
            "total_trades": 0,
            "winning_trades": 0,
            "losing_trades": 0,
            "win_rate": 0.0,
            "net_profit": 0.0,
            "gross_profit": 0.0,
            "gross_loss": 0.0,
            "profit_factor": 0.0,
            "average_trade": 0.0,
            "average_win": 0.0,
            "average_loss": 0.0,
            "largest_win": 0.0,
            "largest_loss": 0.0,
            "max_drawdown": 0.0,
            "sharpe_ratio": 0.0,
            "sortino_ratio": 0.0
        }
