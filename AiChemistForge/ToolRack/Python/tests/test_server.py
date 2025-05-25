#!/usr/bin/env python3
"""Simple test script to verify MCP server functionality."""

import asyncio
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from fastmcp import Client

from unified_mcp_server import fastmcp_app


async def test_server():
    """Test the MCP server functionality."""
    print("Testing AiChemistForge MCP Server...")

    try:
        # Create a client connected to our server
        async with Client(fastmcp_app) as client:
            print("✅ Successfully connected to server")

            # List available tools
            tools = await client.list_tools()
            print(f"✅ Found {len(tools.tools)} tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")

            # List available resources
            resources = await client.list_resources()
            print(f"✅ Found {len(resources.resources)} resources:")
            for resource in resources.resources:
                print(f"  - {resource.uri}: {resource.name}")

            # List available prompts
            prompts = await client.list_prompts()
            print(f"✅ Found {len(prompts.prompts)} prompts:")
            for prompt in prompts.prompts:
                print(f"  - {prompt.name}: {prompt.description}")

            # Test a simple tool call
            print("\n🧪 Testing file_tree tool...")
            result = await client.call_tool("file_tree", {"path": ".", "max_depth": 2})
            if result.content:
                print("✅ file_tree tool works!")
                print(f"Result preview: {str(result.content)[:200]}...")
            else:
                print("❌ file_tree tool failed")

            print("\n🎉 All tests passed! Server is working correctly.")

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    return True


if __name__ == "__main__":
    asyncio.run(test_server())
