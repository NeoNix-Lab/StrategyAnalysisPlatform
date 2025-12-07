import sqlite3
import pandas as pd
from sqlalchemy.orm import Session
from src.database.models import Bar, Order, Execution, Side, OrderType, OrderStatus
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

class SqliteImporter:
    def __init__(self, db_session: Session):
        self.db = db_session

    def import_file(self, file_path: str):
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        logger.info(f"Starting import from {file_path}")
        affected_strategies = set()
        
        try:
            with sqlite3.connect(file_path) as conn:
                self._check_version(conn)
                self._import_bars(conn)
                
                # Create a StrategyRun for this import
                # We need to extract strategy_id from orders first, or assume it's consistent in the file
                # Let's peek at orders to get strategy_id
                cursor = conn.cursor()
                cursor.execute("SELECT strategy_id FROM Orders LIMIT 1")
                row = cursor.fetchone()
                
                run_id = None
                if row:
                    strategy_id = row[0]
                    run_id = self._create_strategy_run(strategy_id, file_path)
                    affected_strategies = self._import_orders(conn, run_id)
                    self._import_executions(conn) # Executions don't need run_id directly, they link to orders
                else:
                    logger.warning("No orders found in file, skipping run creation.")
                
            self.db.commit()
            logger.info("Import completed successfully.")
            return affected_strategies
        except Exception as e:
            self.db.rollback()
            logger.error(f"Import failed: {e}")
            raise

    def _create_strategy_run(self, strategy_id: str, source_file: str) -> str:
        """Creates a new StrategyRun and ensures the Strategy exists."""
        from src.database.models import Strategy, StrategyRun
        import uuid
        import json
        
        # Ensure Strategy exists
        strategy = self.db.query(Strategy).filter(Strategy.strategy_id == strategy_id).first()
        if not strategy:
            strategy = Strategy(strategy_id=strategy_id, name=strategy_id)
            self.db.add(strategy)
            self.db.flush()
            
        # Create Run
        run_id = str(uuid.uuid4())
        run = StrategyRun(
            run_id=run_id,
            strategy_id=strategy_id,
            start_time=datetime.utcnow(),
            status="COMPLETED",
            parameters=json.dumps({"source_file": os.path.basename(source_file)}),
            data_range=None # Could be populated from bars
        )
        self.db.add(run)
        self.db.flush()
        logger.info(f"Created StrategyRun {run_id} for strategy {strategy_id}")
        return run_id

    def _check_version(self, conn: sqlite3.Connection):
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM Metadata WHERE key = 'schema_version'")
            row = cursor.fetchone()
            version = row[0] if row else "1.0"
            logger.info(f"Detected schema version: {version}")
        except sqlite3.OperationalError:
            logger.warning("Metadata table not found, assuming version 1.0")

    def _import_bars(self, conn: sqlite3.Connection):
        df = pd.read_sql_query("SELECT * FROM Bars", conn)
        if df.empty:
            return

        # 1. Identify Symbol and Timeframe
        groups = df.groupby(['symbol', 'timeframe'])

        total_inserted = 0
        total_skipped = 0

        for (symbol, timeframe), group in groups:
            # Parse timestamps for this group
            group['start_time_utc'] = pd.to_datetime(group['start_time_utc'])
            if 'end_time_utc' in group.columns:
                group['end_time_utc'] = pd.to_datetime(group['end_time_utc'])
            else:
                group['end_time_utc'] = group['start_time_utc'] # Fallback

            min_time = group['start_time_utc'].min()
            max_time = group['start_time_utc'].max()

            # 2. Query existing timestamps in this range
            existing_query = self.db.query(Bar.timestamp).filter(
                Bar.symbol == symbol,
                Bar.timeframe == timeframe,
                Bar.timestamp >= min_time,
                Bar.timestamp <= max_time
            )
            existing_timestamps = {row[0] for row in existing_query.all()}

            # 3. Filter out existing records
            new_bars_df = group[~group['start_time_utc'].isin(existing_timestamps)]
            
            skipped_count = len(group) - len(new_bars_df)
            total_skipped += skipped_count

            if new_bars_df.empty:
                continue

            # 4. Bulk Insert
            bars_to_insert = []
            for _, row in new_bars_df.iterrows():
                bar = Bar(
                    symbol=row['symbol'],
                    timeframe=row['timeframe'],
                    timestamp=row['start_time_utc'],
                    end_time=row['end_time_utc'],
                    open=row['open'],
                    high=row['high'],
                    low=row['low'],
                    close=row['close'],
                    volume=row['volume'],
                    open_interest=row.get('open_interest')
                )
                bars_to_insert.append(bar)

            self.db.bulk_save_objects(bars_to_insert)
            total_inserted += len(bars_to_insert)

        logger.info(f"Bars Import Summary: {total_inserted} inserted, {total_skipped} skipped (already existed).")

    def _import_orders(self, conn: sqlite3.Connection, run_id: str):
        df = pd.read_sql_query("SELECT * FROM Orders", conn)
        if df.empty:
            return set()

        logger.info(f"Importing {len(df)} orders...")
        affected = set()
        
        for _, row in df.iterrows():
            submit_time = pd.to_datetime(row['submit_time_utc'])
            
            # Map Enums
            try:
                side = Side[row['side']]
                order_type = OrderType[row['order_type']]
                status = OrderStatus[row['status']]
            except KeyError as e:
                logger.warning(f"Skipping order {row['order_id']} due to invalid enum mapping: {e}")
                continue

            order = Order(
                order_id=row['order_id'],
                parent_order_id=row.get('parent_order_id'),
                strategy_id=row['strategy_id'],
                run_id=run_id, # Link to the new Run
                strategy_version=row.get('strategy_version'),
                account_id=row['account_id'],
                symbol=row['symbol'],
                side=side,
                order_type=order_type,
                time_in_force=row.get('time_in_force'),
                submit_time=submit_time,
                price=row.get('price'),
                stop_price=row.get('stop_price'),
                quantity=row['quantity'],
                status=status,
                reject_reason=row.get('reject_reason'),
                cancel_reason=row.get('cancel_reason'),
                client_tag=row.get('client_tag'),
                meta_json=row.get('meta_json')
            )
            self.db.merge(order)
            
            if row.get('strategy_id') and row.get('symbol'):
                affected.add((row['strategy_id'], row['symbol']))
                
        return affected

    def _import_executions(self, conn: sqlite3.Connection):
        df = pd.read_sql_query("SELECT * FROM Executions", conn)
        if df.empty:
            return

        logger.info(f"Importing {len(df)} executions...")
        
        for _, row in df.iterrows():
            exec_time = pd.to_datetime(row['exec_time_utc'])
            
            try:
                side = Side[row['side']]
            except KeyError:
                logger.warning(f"Skipping execution {row['execution_id']} due to invalid side: {row['side']}")
                continue

            execution = Execution(
                execution_id=row['execution_id'],
                order_id=row['order_id'],
                strategy_id=row.get('strategy_id'),
                account_id=row.get('account_id'),
                symbol=row['symbol'],
                side=side,
                exec_time=exec_time,
                price=row['price'],
                quantity=row['quantity'],
                fee=row.get('fee', 0.0),
                fee_currency=row.get('fee_currency'),
                liquidity_flag=row.get('liquidity_flag')
            )
            self.db.merge(execution)
