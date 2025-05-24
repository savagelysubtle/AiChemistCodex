#!/usr/bin/env python3
"""
Test script for the AiChemistForge MCP server.
"""

import asyncio
import sys
from pathlib import Path

# Add the src directory to Python path for testing
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def test_server_import():
    """Test that the server can be imported successfully."""
    try:
        from unified_mcp_server.server import config, fastmcp_app
        from unified_mcp_server.tools import ToolRegistry
        from unified_mcp_server.resources import resource_registry
        from unified_mcp_server.prompts import prompt_registry

        print("✓ Server imports successful")
        print(f"✓ Config loaded: {config.server_name}")

        # Test FastMCP app
        print(f"✓ FastMCP app initialized: {fastmcp_app.name}")

        # Test tool registry
        registry = ToolRegistry()
        print("✓ Tool registry created")

        # Test resource registry
        print("✓ Resource registry imported")

        # Test prompt registry
        print("✓ Prompt registry imported")

        # Test tool discovery
        await registry.initialize_tools()
        tools = registry.get_all_tools()
        print(f"✓ Tools discovered: {len(tools)} tools")

        for tool_name in tools:
            print(f"  - {tool_name}")

        # Test resource discovery
        await resource_registry.initialize_resources()
        resources = resource_registry.get_all_resources()
        print(f"✓ Resources discovered: {len(resources)} resources")

        for resource_uri in resources:
            print(f"  - {resource_uri}")

        # Test prompt discovery
        await prompt_registry.initialize_prompts()
        prompts = prompt_registry.get_all_prompts()
        print(f"✓ Prompts discovered: {len(prompts)} prompts")

        for prompt_name in prompts:
            print(f"  - {prompt_name}")

        print("\n✓ All tests passed!")
        return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_tool_execution():
    """Test tool execution."""
    try:
        from unified_mcp_server.tools import ToolRegistry

        registry = ToolRegistry()
        await registry.initialize_tools()

        # Test cursor_db tool if available
        cursor_tool = registry.get_tool("cursor_db")
        if cursor_tool:
            print("✓ Found cursor_db tool")

            # Test listing projects
            result = await cursor_tool.safe_execute(operation="list_projects")
            print(f"✓ List projects result: {result['success']}")

            if result['success']:
                projects = result['result']
                print(f"  Found {len(projects)} projects")
        else:
            print("ℹ cursor_db tool not available")

        return True

    except Exception as e:
        print(f"✗ Tool execution error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_resources_and_prompts():
    """Test resources and prompts functionality."""
    try:
        from unified_mcp_server.resources import resource_registry
        from unified_mcp_server.prompts import prompt_registry

        # Test resources
        await resource_registry.initialize_resources()
        resources = resource_registry.get_all_resources()

        if "cursor://projects" in resources:
            print("✓ Found cursor projects resource")

            # Test the resource
            handler = resource_registry.get_resource_handler("cursor://projects")
            if handler:
                result = await handler()
                print(f"✓ Resource executed successfully: {len(result.get('contents', []))} items")

        # Test prompts
        await prompt_registry.initialize_prompts()
        prompts = prompt_registry.get_all_prompts()

        if "explore_cursor_projects" in prompts:
            print("✓ Found explore cursor projects prompt")

            # Test the prompt
            handler = prompt_registry.get_prompt_handler("explore_cursor_projects")
            if handler:
                result = await handler()
                print(f"✓ Prompt executed successfully: {result.get('description', 'No description')}")

        return True

    except Exception as e:
        print(f"✗ Resources/Prompts error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Run all tests."""
    print("AiChemistForge MCP Server Test")
    print("=" * 40)

    # Test imports
    print("\n1. Testing imports...")
    if not await test_server_import():
        return 1

    # Test tool execution
    print("\n2. Testing tool execution...")
    if not await test_tool_execution():
        return 1

    # Test resources and prompts
    print("\n3. Testing resources and prompts...")
    if not await test_resources_and_prompts():
        return 1

    print("\n🎉 All tests completed successfully!")
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⚠️  Test interrupted")
        sys.exit(1)