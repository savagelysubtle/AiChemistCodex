"""
Server infrastructure for the unified MCP server.

This module contains the core server components including configuration,
logging, lifecycle management, and the FastMCP application setup.
"""

from .config import config, ServerConfig
from .logging import setup_logging
from .app import fastmcp_app, create_fastmcp_app
from .lifecycle import lifecycle_manager, LifecycleManager

__all__ = [
    "config",
    "ServerConfig",
    "setup_logging",
    "fastmcp_app",
    "create_fastmcp_app",
    "lifecycle_manager",
    "LifecycleManager"
]