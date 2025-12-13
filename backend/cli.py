import argparse
import logging
from src.database.connection import SessionLocal
from src.etl.import_sqlite import SqliteImporter

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Strategy Analysis Platform CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Import Command
    import_parser = subparsers.add_parser("import", help="Import data from SQLite export")
    import_parser.add_argument("--file", required=True, help="Path to the SQLite file")

    args = parser.parse_args()

from src.core.trade_builder import TradeBuilder

# ...

    if args.command == "import":
        db = SessionLocal()
        try:
            importer = SqliteImporter(db)
            affected = importer.import_file(args.file)
            
            if affected:
                print(f"Triggering trade reconstruction for {len(affected)} strategies...")
                builder = TradeBuilder(db)
                for strategy_id, symbol in affected:
                    builder.reconstruct_trades(strategy_id, symbol)
                print("Trade reconstruction completed.")
                
        except Exception as e:
            logger.error(f"Error during import: {e}")
        finally:
            db.close()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
