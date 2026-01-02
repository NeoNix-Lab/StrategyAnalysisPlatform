import logging
import sys
import os
from logging.handlers import RotatingFileHandler

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
