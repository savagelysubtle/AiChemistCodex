"""
Server infrastructure for the unified MCP server.

This module contains the core server components including configuration,
logging, lifecycle management, and the FastMCP application setup.
"""

from .config import ServerConfig, config

# Remove app imports to avoid circular dependency
# from .app import fastmcp_app, create_fastmcp_app
# Remove lifecycle import to avoid circular dependency
# from .lifecycle import LifecycleManager, lifecycle_manager
from .logging import setup_logging


# Lazy imports to avoid circular dependency
def get_fastmcp_app():
    """Get the FastMCP app instance (lazy import)."""
    from .app import fastmcp_app

    return fastmcp_app


def create_fastmcp_app():
    """Create FastMCP app instance (lazy import)."""
    from .app import create_fastmcp_app as _create_fastmcp_app

    return _create_fastmcp_app()


def get_lifecycle_manager():
    """Get the lifecycle manager instance (lazy import)."""
    from .lifecycle import lifecycle_manager

    return lifecycle_manager


def get_lifecycle_manager_class():
    """Get the LifecycleManager class (lazy import)."""
    from .lifecycle import LifecycleManager

    return LifecycleManager


__all__ = [
    "config",
    "ServerConfig",
    "setup_logging",
    "get_fastmcp_app",
    "create_fastmcp_app",
    "get_lifecycle_manager",
    "get_lifecycle_manager_class",
]
