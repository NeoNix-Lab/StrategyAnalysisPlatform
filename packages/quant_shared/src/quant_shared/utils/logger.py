import logging
import sys
import os
from logging.handlers import RotatingFileHandler

def _ensure_contracts_on_path():
    packages_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "../../../../../packages"))
    if packages_dir not in sys.path:
        sys.path.insert(0, packages_dir)

def get_logger(name: str, log_file: str = "app.log", level: str = None) -> logging.Logger:
    """
    Creates and configures a logger instance.
    
    Args:
        name: Name of the logger (usually __name__)
        log_file: Path to log file (default: app.log)
        level: Logging level (default: read from env LOG_LEVEL or INFO)
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Defaults
    env_level = os.getenv("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, level.upper()) if level else getattr(logging, env_level, logging.INFO)
    
    logger.setLevel(log_level)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
        
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console Handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(log_level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File Handler (Optional, if LOG_FILE_PATH set or explicit log_file provided)
    log_path = os.getenv("LOG_FILE_PATH", log_file)
    if log_path:
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(os.path.abspath(log_path)), exist_ok=True)
            
            fh = RotatingFileHandler(
                log_path, 
                maxBytes=10*1024*1024, # 10MB
                backupCount=5
            )
            fh.setLevel(log_level)
            fh.setFormatter(formatter)
            logger.addHandler(fh)
        except Exception as e:
            print(f"Failed to setup file logging: {e}")
            
            
    return logger

def attach_queue_handler(logger: logging.Logger, queue):
    """
    Attaches a QueueHandler to the logger to stream logs to an asyncio or multiprocessing queue.
    """
    from logging.handlers import QueueHandler
    import json
    
    # Check if already attached
    for h in logger.handlers:
        if isinstance(h, QueueHandler):
            return
            
    # Custom QueueHandler that formats to Contract before putting
    class ContractQueueHandler(QueueHandler):
        def emit(self, record: logging.LogRecord):
            try:
                # Basic formatting from internal LogRecord to Contract
                # We do this HERE to ensure what goes into the queue is already compliant 
                # (or at least close to it, though usually QueueHandler puts the raw record).
                
                # However, standard QueueHandler just puts the 'record' object.
                # If we want to strictly enforce the contract, we should probably 
                # convert it at the CONSUMER side (system.py) or here.
                # Converting here means we assume the queue transports dicts/JSON strings, not LogRecord objects.
                # If the queue is expected to transport standard LogRecords (for other standard listeners), 
                # we should keep it standard.
                # BUT, for our specific "Log Stream" use case, sending a Pydantic model or dict is safer.
                
                # Let's keep the standard behavior of QueueHandler (sending LogRecord) 
                # and do the conversion in the consumer (system.py).
                # This keeps the logger generic. 
                # Wait, the task says "Update logger.py to use new contracts". 
                # Maybe I should just ensure the formatter produces the right structure?
                
                # Actually, standard python logging QueueHandler expects to put the LogRecord object.
                # Let's stick to standard and update system.py to use the contract for validation/serialization.
                # But I will add the import here to verify it's available.
                pass
                
            except Exception:
                self.handleError(record)
                
            super().emit(record)

    # Use standard QueueHandler for now to be safe with standard python logging flows.
    # The conversion happens in the router.
    qh = QueueHandler(queue)
    qh.setLevel(logging.INFO)
    
    # Custom formatter for JSON-like structure if needed, or just standard
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    qh.setFormatter(formatter)
    
    logger.addHandler(qh)

class HttpLogHandler(logging.Handler):
    """
    Log handler that sends logs to an HTTP endpoint (API Gateway).
    Uses a background worker thread to process a queue and avoid blocking the main thread.
    """
    def __init__(self, url: str, service_name: str, token: str = None):
        super().__init__()
        self.url = url
        self.service_name = service_name
        self.token = token
        
        # Internal queue for the worker
        from queue import Queue
        self.queue = Queue()
        
        # Start worker thread
        import threading
        self._stop_event = threading.Event()
        self.worker = threading.Thread(target=self._monitor_queue, daemon=True)
        self.worker.start()

    def emit(self, record: logging.LogRecord):
        try:
            self.queue.put(record)
        except Exception:
            self.handleError(record)

    def _monitor_queue(self):
        import requests
        try:
            from quant_shared.schemas.logging import LogRecord
        except ImportError:
            # Fallback for dev environment issues
            raise
        from datetime import datetime

        session = requests.Session()
        if self.token:
            session.headers.update({"Authorization": f"Bearer {self.token}"})
        
        while not self._stop_event.is_set():
            try:
                # Block for 1 sec then check stop event
                record = self.queue.get(timeout=1.0)
                
                # Convert to Contract
                try:
                    contract_log = LogRecord(
                        timestamp=datetime.fromtimestamp(record.created),
                        level=record.levelname,
                        name=self.service_name, # Use service name as override or record.name? record.name is better for granularity
                        message=record.getMessage(),
                        meta={
                            "logger_name": record.name,
                            "filename": record.filename,
                            "lineno": record.lineno
                        }
                    )
                    payload = contract_log.json()
                    # Send pre-serialized JSON so datetime is already ISO-encoded
                    response = session.post(
                        self.url,
                        data=payload,
                        timeout=2,
                        headers={"Content-Type": "application/json"}
                    )
                    if response.status_code >= 400:
                        print(f"Failed to send log to gateway: {response.text}")
                        
                except Exception as e:
                    # Don't crash the worker
                    print(f"Error sending log: {e}")
                finally:
                    self.queue.task_done()
                    
            except Exception:
                # Empty queue timeout
                continue

    def close(self):
        self._stop_event.set()
        if self.worker.is_alive():
            self.worker.join(timeout=2.0)
        super().close()

def setup_remote_logging(logger_name: str, gateway_url: str, service_name: str):
    """
    Helper to configure a logger to send logs to the central gateway.
    """
    logger = logging.getLogger(logger_name)
    
    # Check if already has handler
    for h in logger.handlers:
        if isinstance(h, HttpLogHandler):
            return logger
            
    handler = HttpLogHandler(f"{gateway_url}/internal/logs", service_name)
    handler.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger
