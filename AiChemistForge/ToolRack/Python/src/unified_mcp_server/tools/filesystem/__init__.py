"""Filesystem tools for the unified MCP server."""

from .base import BaseFilesystemTool, FilesystemError, PathTraversalError
from .codebase_ingest import CodebaseIngestTool
from .file_tree import FileTreeTool

# Auto-discovery for tool registry
__all__ = [
    "BaseFilesystemTool",
    "FilesystemError",
    "PathTraversalError",
    "FileTreeTool",
    "CodebaseIngestTool",
]
