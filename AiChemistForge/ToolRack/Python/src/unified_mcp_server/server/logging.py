"""Logging setup for the unified MCP server."""

import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logging(
    name: str,
    level: str = "INFO",
    log_to_file: bool = False,
    log_file_path: Optional[Path] = None
) -> logging.Logger:
    """Set up structured logging for MCP server components.

    Args:
        name: Logger name (typically module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to log to file in addition to stderr
        log_file_path: Path to log file (defaults to logs/{name}.log)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler (stderr for MCP compatibility)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (optional)
    if log_to_file:
        if log_file_path is None:
            log_file_path = Path("logs") / f"{name}.log"

        log_file_path.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger