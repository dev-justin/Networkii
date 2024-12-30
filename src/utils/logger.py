import os
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

# Global flag to track if logger has been initialized
_initialized = False

def init_logging():
    """Initialize the application logger if not already initialized"""
    global _initialized
    if _initialized:
        return

    # Set up logging directory in /var/log
    LOG_DIR = '/var/log/networkii'
    LOG_FILE = os.path.join(LOG_DIR, 'networkii.log')
    MAX_LOG_SIZE = 5 * 1024 * 1024  # 5 MB

    # Create log directory with proper permissions
    try:
        os.makedirs(LOG_DIR, exist_ok=True)
        os.chmod(LOG_DIR, 0o777)  # Ensure directory is writable
    except Exception as e:
        print(f"Error setting up log directory: {e}")
        # Fallback to current directory if we can't write to /var/log
        LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'logs')
        LOG_FILE = os.path.join(LOG_DIR, 'networkii.log')
        os.makedirs(LOG_DIR, exist_ok=True)

    # Configure the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # Create rotating file handler that keeps only one file
    handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_LOG_SIZE,
        backupCount=0  # No backup files, just rotate the main file
    )
    handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    root_logger.addHandler(handler)

    # Log initial setup
    logger = logging.getLogger('logger_setup')
    logger.info("Logging configured to: %s (max size: %d bytes)", LOG_FILE, MAX_LOG_SIZE)
    
    _initialized = True

def get_logger(name):
    """Get a logger instance, initializing logging if needed"""
    if not _initialized:
        init_logging()
    return logging.getLogger(name)

# Initialize logging when module is imported
init_logging() 