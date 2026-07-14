"""Logging utility module for the Smart PDF Assistant.

Sets up standard Python logging configurations using settings defined in 
the configuration layer.
"""

import logging
import sys
from backend.app.config import settings

def setup_logging() -> None:
    """Configures the root logger for the application.
    
    Sets the log level according to settings.LOG_LEVEL and adds stdout 
    and file handlers with a consistent format:
    timestamp - log level - module name - message
    """
    # Parse log level string to logging constant
    log_level_str = settings.LOG_LEVEL.upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Define consistent format
    log_format = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    formatter = logging.Formatter(log_format, datefmt=date_format)

    # Configure stdout stream handler
    stdout_handler = logging.StreamHandler(sys.stdout)
    stdout_handler.setFormatter(formatter)

    # Configure file handler
    file_handler = logging.FileHandler(settings.LOG_FILE_PATH, encoding="utf-8")
    file_handler.setFormatter(formatter)

    # Get root logger
    root_logger = logging.getLogger()
    
    # Clear existing handlers to prevent duplicate logs if re-initialized
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.setLevel(log_level)
    root_logger.addHandler(stdout_handler)
    root_logger.addHandler(file_handler)

    # Log initial configuration setup message
    logging.getLogger(__name__).info(
        f"Logging initialized. Level: {log_level_str}, Log File: {settings.LOG_FILE_PATH}"
    )


# Automatically initialize logging when this module is imported
setup_logging()
