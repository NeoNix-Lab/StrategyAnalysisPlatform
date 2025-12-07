from sqlalchemy.orm import Session
from src.database.models import Execution, Trade, Side
import uuid

class TradeBuilder:
    def __init__(self, db_session: Session):
        self.db = db_session

    def reconstruct_trades(self, strategy_id: str, symbol: str):
        """
        Ricostruisce i trade (Round-Turn) partendo dalle esecuzioni usando logica FIFO.
        """
        # 1. Recupera tutte le esecuzioni per strategia/simbolo ordinate per tempo
        executions = self.db.query(Execution).filter(
            Execution.strategy_id == strategy_id,
            Execution.symbol == symbol
        ).order_by(Execution.exec_time).all()

        open_positions = [] # Lista di dizionari: {'qty': float, 'price': float, 'time': datetime, 'side': Side}
        closed_trades = []

        print(f"Analisi {len(executions)} esecuzioni per {symbol}...")

        for exec in executions:
            qty_remaining = exec.quantity
            
            # Se non abbiamo posizioni aperte o il lato è lo stesso, aggiungiamo alla "pila" (Open Position)
            if not open_positions or open_positions[0]['side'] == exec.side:
                open_positions.append({
                    'qty': exec.quantity,
                    'price': exec.price,
                    'time': exec.exec_time,
                    'side': exec.side,
                    'commission': exec.fee # Semplificazione: attribuiamo fee all'apertura per ora
                })
                continue

            # Se siamo qui, stiamo chiudendo una posizione (lato opposto)
            while qty_remaining > 0 and open_positions:
                opening_pos = open_positions[0] # FIFO: prendiamo il primo
                
                matched_qty = min(qty_remaining, opening_pos['qty'])
                
                # Calcolo PnL
                # Se LONG: (Exit - Entry) * Qty
                # Se SHORT: (Entry - Exit) * Qty
                if opening_pos['side'] == Side.BUY: # Chiudiamo un LONG con una SELL
                    pnl_gross = (exec.price - opening_pos['price']) * matched_qty
                    trade_side = Side.BUY
                else: # Chiudiamo uno SHORT con una BUY
                    pnl_gross = (opening_pos['price'] - exec.price) * matched_qty
                    trade_side = Side.SELL

                # Creazione oggetto Trade
                trade = Trade(
                    trade_id=str(uuid.uuid4()),
                    strategy_id=strategy_id,
                    symbol=symbol,
                    side=trade_side,
                    entry_time=opening_pos['time'],
                    exit_time=exec.exec_time,
                    entry_price=opening_pos['price'],
                    exit_price=exec.price,
                    quantity=matched_qty,
                    pnl_gross=pnl_gross,
                    pnl_net=pnl_gross - (opening_pos['commission'] * (matched_qty/opening_pos['qty']) + exec.fee * (matched_qty/exec.quantity)), # Stima commissioni pro-quota
                    commission=(opening_pos['commission'] * (matched_qty/opening_pos['qty']) + exec.fee * (matched_qty/exec.quantity)),
                    duration_seconds=(exec.exec_time - opening_pos['time']).total_seconds()
                )
                closed_trades.append(trade)

                # Aggiornamento quantità
                qty_remaining -= matched_qty
                opening_pos['qty'] -= matched_qty
                
                if opening_pos['qty'] <= 0.000001: # Float tolleranza
                    open_positions.pop(0) # Rimuoviamo la posizione esaurita

        # Salvataggio nel DB
        try:
            # Opzionale: cancellare vecchi trade per questa strategia/simbolo per evitare duplicati in fase di ricalcolo
            self.db.query(Trade).filter(Trade.strategy_id == strategy_id, Trade.symbol == symbol).delete()
            
            self.db.bulk_save_objects(closed_trades)
            self.db.commit()
            print(f"✅ Ricostruiti {len(closed_trades)} trade.")
        except Exception as e:
            self.db.rollback()
            print(f"❌ Errore salvataggio trade: {e}")
            
        return closed_trades
