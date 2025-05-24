"""
MCP Prompts for the unified server.

This module contains prompt implementations organized by category
for various analysis and workflow tasks.
"""

from .registry import prompt_registry, PromptRegistry

__all__ = [
    "prompt_registry",
    "PromptRegistry"
]