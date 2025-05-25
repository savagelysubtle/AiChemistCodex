"""
AiChemistForge - Unified MCP Server with integrated reasoning tools.

This package provides a unified MCP server built with FastMCP that includes:
- File system analysis tools (file_tree, codebase_ingest)
- Cursor IDE database integration
- Plugin management system
- Built-in sequential thinking and reasoning capabilities

The server uses a single FastMCP instance with @mcp.tool(), @mcp.resource(),
and @mcp.prompt() decorators for clean, efficient operation.
"""

__version__ = "1.0.0"
__author__ = "Steve"
__email__ = "steve@simpleflowworks.com"

# Export the main FastMCP app for external use
from .main import mcp as fastmcp_app

__all__ = ["fastmcp_app"]
