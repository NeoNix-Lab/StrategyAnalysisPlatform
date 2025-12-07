import pandas as pd
from sqlalchemy.orm import Session
from src.database.models import Bar, Order, Execution, Side, OrderType, OrderStatus
from datetime import datetime
import json

class DataImporter:
    def __init__(self, db_session: Session):
        self.db = db_session

    def import_bars_from_csv(self, file_path: str, symbol: str, timeframe: str):
        """
        Importa barre da un CSV. 
        Si aspetta colonne: timestamp, open, high, low, close, volume
        """
        df = pd.read_csv(file_path)
        
        # Normalizzazione nomi colonne (basic)
        df.columns = [c.lower().strip() for c in df.columns]
        
        bars_to_add = []
        for _, row in df.iterrows():
            # Parsing timestamp (da adattare in base al formato input)
            try:
                ts = pd.to_datetime(row['timestamp'])
            except KeyError:
                # Fallback se la colonna si chiama 'date' o 'time'
                ts = pd.to_datetime(row.get('date', row.get('time')))

            bar = Bar(
                symbol=symbol,
                timeframe=timeframe,
                timestamp=ts,
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row['volume'],
                open_interest=row.get('open_interest', 0)
            )
            bars_to_add.append(bar)
        
        # Bulk save per performance
        try:
            self.db.bulk_save_objects(bars_to_add)
            self.db.commit()
            print(f"Importate {len(bars_to_add)} barre per {symbol} [{timeframe}]")
        except Exception as e:
            self.db.rollback()
            print(f"Errore durante import barre: {e}")

    def import_orders_from_json(self, file_path: str):
        """Esempio di import ordini da JSON."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        for item in data:
            # Qui andrebbe aggiunta validazione (es. Pydantic)
            order = Order(
                order_id=item['order_id'],
                strategy_id=item['strategy_id'],
                symbol=item['symbol'],
                side=Side[item['side']],
                order_type=OrderType[item['order_type']],
                quantity=item['quantity'],
                price=item.get('price'),
                status=OrderStatus[item['status']]
                # ... altri campi
            )
            self.db.merge(order) # Merge per evitare duplicati se order_id esiste
        
        self.db.commit()
        print(f"Processati {len(data)} ordini.")

    # TODO: Aggiungere import_executions
