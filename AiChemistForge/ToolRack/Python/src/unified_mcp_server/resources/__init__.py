"""
MCP Resources for the unified server.

This module contains resource implementations organized by category
for exposing various data sources and endpoints.
"""

from .registry import resource_registry, ResourceRegistry

__all__ = [
    "resource_registry",
    "ResourceRegistry"
]