"""
Server infrastructure for the unified MCP server.

This module contains basic configuration and logging utilities.
The main FastMCP server is now defined directly in main.py.
"""

from .config import ServerConfig, config
from .logging import setup_logging

__all__ = ["config", "ServerConfig", "setup_logging"]
