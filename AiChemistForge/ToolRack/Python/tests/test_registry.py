#!/usr/bin/env python3
"""Test script for tool registry."""

import asyncio

import pytest

from unified_mcp_server.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_registry_initialization():
    """Test tool registry initialization."""
    print("Testing tool registry initialization...")
    registry = ToolRegistry()

    await registry.initialize_tools()
    tools = registry.get_all_tools()

    # Assert that tools were loaded
    assert len(tools) > 0, "Should load at least one tool"

    print(f"Successfully loaded {len(tools)} tools:")
    for name, tool in tools.items():
        print(f"  - {name}: {tool.description}")


# For backwards compatibility, keep the main function for direct execution
async def main():
    """Run registry test."""
    try:
        await test_registry_initialization()
    except Exception as e:
        print(f"Error initializing tools: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
