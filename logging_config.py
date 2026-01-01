"""
Centralized logging configuration for DashFleet.
Provides consistent logging across all modules.
"""

import logging
import sys
from pathlib import Path

# Default log paths
LOG_PATH = Path("logs/api.log")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def setup_logging(
    log_file: str | Path = LOG_PATH,
    level: int = logging.INFO,
    console: bool = False,
    format_string: str | None = None,
) -> logging.Logger:
    """
    Configure logging for DashFleet.
    
    Args:
        log_file: Path to log file (default: logs/api.log)
        level: Logging level (default: INFO)
        console: Also log to console stdout (default: False)
        format_string: Custom format string (default: standard ISO format)
    
    Returns:
        Configured root logger
    """
    if format_string is None:
        format_string = "%(asctime)s %(levelname)s %(message)s"
    
    # Create formatter
    formatter = logging.Formatter(format_string)
    
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # File handler
    file_handler = logging.FileHandler(str(log_file))
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler (optional)
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a named logger for modules."""
    return logging.getLogger(name)


# Initialize default logging on import
setup_logging()
