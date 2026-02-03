"""Logging configuration for the CLI target cleanup tool."""

import logging
import sys
from typing import Optional


def setup_logging(verbose: bool = False) -> logging.Logger:
    """
    Configure and return a logger for the application.
    
    Args:
        verbose: If True, set log level to DEBUG. Otherwise, INFO.
        
    Returns:
        Configured logger instance.
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    
    # Create logger
    logger = logging.getLogger("cli-target-cleanup")
    logger.setLevel(log_level)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(console_handler)
    
    return logger


def get_logger() -> logging.Logger:
    """
    Get the application logger.
    
    Returns:
        The application logger instance.
    """
    return logging.getLogger("cli-target-cleanup")
