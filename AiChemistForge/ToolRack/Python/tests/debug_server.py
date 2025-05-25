#!/usr/bin/env python3
"""Debug script to test MCP server startup."""

import asyncio
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_fastmcp_startup():
    """Test FastMCP server startup."""
    try:
        print("🔧 Testing FastMCP startup...")

        from unified_mcp_server.server.app import create_fastmcp_app

        # Create the app
        print("Creating FastMCP app...")
        app = create_fastmcp_app()

        print("✅ FastMCP app created successfully")
        return True

    except Exception as e:
        print(f"❌ FastMCP startup failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_tool_registry():
    """Test tool registry initialization."""
    try:
        print("🔧 Testing tool registry...")

        from unified_mcp_server.tools.registry import ToolRegistry

        registry = ToolRegistry()

        # Test with timeout
        print("Initializing tools with 3 second timeout...")
        await asyncio.wait_for(registry.initialize_tools(), timeout=3.0)

        tools = registry.get_all_tools()
        print(f"✅ Registered {len(tools)} tools: {list(tools.keys())}")
        return True

    except asyncio.TimeoutError:
        print("❌ Tool registry initialization timed out")
        return False
    except Exception as e:
        print(f"❌ Tool registry failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run debug tests."""
    print("🚀 MCP Server Debug Tests")
    print("=" * 40)

    tests = [
        ("Tool Registry", test_tool_registry),
        ("FastMCP Startup", test_fastmcp_startup),
    ]

    for name, test_func in tests:
        print(f"\n{name}:")
        result = await test_func()
        print()

    print("=" * 40)
    print("Debug tests completed")


if __name__ == "__main__":
    asyncio.run(main())
