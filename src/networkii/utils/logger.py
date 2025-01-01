import os
import logging
from pathlib import Path

def get_logger(name):
    """Get a logger instance with the specified name."""
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Only add handler if it doesn't have one
        logger.setLevel(logging.DEBUG)
        
        # Create user-specific log directory
        log_dir = Path.home() / '.local' / 'log' / 'networkii'
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = str(log_dir / 'networkii.log')
        
        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.ERROR)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger 