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
