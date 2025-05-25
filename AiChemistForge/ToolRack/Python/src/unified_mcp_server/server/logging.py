"""Logging setup for the unified MCP server.

Following 1000-mcp-stdio-logging.mdc guidelines:
- Keep logging simple for local MCP servers
- Direct logs to stderr to avoid stdio JSON-RPC interference
- Prioritize simplicity over complex logging frameworks
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_simple_logging(
    name: str, level: str = "INFO", use_stderr: bool = True
) -> logging.Logger:
    """Set up simple logging for MCP server components.

    Per 1000-mcp-stdio-logging.mdc: Keep local server logging straightforward.

    Args:
        name: Logger name (typically module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        use_stderr: Whether to use stderr (recommended for MCP stdio compatibility)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level.upper()))

    # Simple formatter - avoid complexity per MCP guidelines
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s", datefmt="%H:%M:%S"
    )

    # Use stderr to keep stdout clear for JSON-RPC (MCP stdio transport requirement)
    stream = sys.stderr if use_stderr else sys.stdout
    handler = logging.StreamHandler(stream)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def setup_logging(
    name: str,
    level: str = "INFO",
    log_to_file: bool = False,
    log_file_path: Optional[Path] = None,
) -> logging.Logger:
    """Set up structured logging for MCP server components.

    This function provides backward compatibility while encouraging
    the use of setup_simple_logging() for new code.

    Args:
        name: Logger name (typically module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_to_file: Whether to log to file in addition to stderr
        log_file_path: Path to log file (defaults to logs/{name}.log)

    Returns:
        Configured logger instance
    """
    # For local MCP servers, prefer simple logging per 1000-mcp-stdio-logging.mdc
    if not log_to_file:
        return setup_simple_logging(name, level)

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (stderr for MCP compatibility)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler (when specifically requested)
    if log_to_file:
        if log_file_path is None:
            log_file_path = Path("logs") / f"{name}.log"

        log_file_path.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str, level: str = "INFO") -> logging.Logger:
    """Get a simple logger for MCP components.

    Convenience function that follows MCP stdio logging best practices.

    Args:
        name: Logger name
        level: Logging level

    Returns:
        Configured logger instance
    """
    return setup_simple_logging(name, level)
