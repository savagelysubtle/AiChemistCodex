"""
Plugin system for the unified MCP server.

This module enables dynamic loading of external tools without modifying
the core server, following MCP protocol specifications and best practices.
"""

from .base import BasePlugin, PluginMetadata, PluginStatus
from .discovery import PluginDiscovery
from .registry import PluginRegistry
from .security import PluginPermission, PluginSecurity

__all__ = [
    "BasePlugin",
    "PluginMetadata",
    "PluginStatus",
    "PluginDiscovery",
    "PluginRegistry",
    "PluginSecurity",
    "PluginPermission",
]
