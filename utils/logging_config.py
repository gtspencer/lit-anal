"""Logging configuration for the book character influence analyzer."""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(log_file: Optional[str] = None, log_level: str = "INFO") -> logging.Logger:
    """Set up logging configuration.
    
    Args:
        log_file: Optional path to log file. If None, only logs to console.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger("litAnal")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always present)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (if log_file specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(getattr(logging, log_level.upper()))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def get_logger(name: str = "litAnal") -> logging.Logger:
    """Get a logger instance.
    
    Args:
        name: Logger name (defaults to "litAnal")
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)

