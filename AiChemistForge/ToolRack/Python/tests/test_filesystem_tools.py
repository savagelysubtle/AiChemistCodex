#!/usr/bin/env python3
"""Test script for filesystem tools."""

import asyncio

import pytest

# Import ToolRegistry from the proper package path
from unified_mcp_server.tools.registry import ToolRegistry


@pytest.mark.asyncio
async def test_tool_discovery():
    """Test that our filesystem tools are discovered."""
    print("🔍 Testing tool discovery...")

    registry = ToolRegistry()
    await registry.initialize_tools()

    tools = registry.get_all_tools()
    print(f"✅ Discovered {len(tools)} tools:")

    for name, tool in tools.items():
        print(f"  - {name}: {tool.description}")

    # Check for our specific tools
    file_tree_tool = registry.get_tool("file_tree")
    codebase_ingest_tool = registry.get_tool("codebase_ingest")

    assert file_tree_tool is not None, "File tree tool should be discovered"
    assert codebase_ingest_tool is not None, "Codebase ingest tool should be discovered"

    print("✅ File tree tool found!")
    print("✅ Codebase ingest tool found!")

    return tools


@pytest.mark.asyncio
async def test_file_tree_tool():
    """Test the file tree tool."""
    print("\n🌳 Testing file tree tool...")

    registry = ToolRegistry()
    await registry.initialize_tools()

    file_tree_tool = registry.get_tool("file_tree")
    assert file_tree_tool is not None, "File tree tool should be available"

    # Test with current directory, limited depth
    result = await file_tree_tool.safe_execute(
        path=".", max_depth=2, show_hidden=False, format="tree"
    )

    assert result["success"], (
        f"File tree generation should succeed: {result.get('error', '')}"
    )

    print("✅ File tree generation successful!")
    print("📁 Directory structure:")
    output = result["result"]
    print(output[:500] + "..." if len(output) > 500 else output)


@pytest.mark.asyncio
async def test_codebase_ingest_tool():
    """Test the codebase ingest tool."""
    print("\n📚 Testing codebase ingest tool...")

    registry = ToolRegistry()
    await registry.initialize_tools()

    codebase_tool = registry.get_tool("codebase_ingest")
    assert codebase_tool is not None, "Codebase ingest tool should be available"

    # Test with current directory, limited files
    result = await codebase_tool.safe_execute(
        path="src",  # Use src directory which should exist
        max_files=5,
        max_file_size=50000,  # 50KB limit for testing
        output_format="structured",
        include_patterns=["*.py"],
    )

    assert result["success"], (
        f"Codebase ingestion should succeed: {result.get('error', '')}"
    )

    print("✅ Codebase ingestion successful!")
    data = result["result"]
    print(f"📊 Found {data['total_files']} files ({data['text_files']} text files)")
    print(f"📏 Total size: {data.get('total_size', 0)} bytes")

    if "tree_structure" in data:
        print("🌳 Tree structure included!")

    # Show first file content preview
    if data["files"] and data["files"][0].get("content"):
        first_file = data["files"][0]
        print(f"📄 First file: {first_file['path']} ({first_file['line_count']} lines)")


# For backwards compatibility, keep the main function for direct execution
async def main():
    """Run all tests."""
    print("🚀 Testing Filesystem Tools for Unified MCP Server")
    print("=" * 50)

    try:
        # Test discovery
        tools = await test_tool_discovery()

        # Test individual tools
        await test_file_tree_tool()
        await test_codebase_ingest_tool()

        print("\n✅ All tests completed!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
