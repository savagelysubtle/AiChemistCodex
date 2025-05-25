#!/usr/bin/env python3
"""Test script to verify MCP server functionality."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path


async def test_server_startup():
    """Test that the server starts up correctly."""
    print("🔧 Testing server startup...")

    cmd = [sys.executable, "-m", "unified_mcp_server.main", "--transport", "stdio"]

    try:
        # Start the server process
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent / "src",
        )

        # Send an initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        # Send the request
        request_str = json.dumps(init_request) + "\n"
        process.stdin.write(request_str)
        process.stdin.flush()

        # Wait for response (with timeout)
        try:
            stdout, stderr = process.communicate(timeout=10)

            if process.returncode == 0:
                print("✅ Server started successfully")
                return True
            else:
                print(f"❌ Server failed with return code: {process.returncode}")
                print(f"STDERR: {stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Server startup timed out")
            process.kill()
            return False

    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return False


def test_mcp_config():
    """Test that the MCP configuration is valid."""
    print("🔧 Testing MCP configuration...")

    config_path = Path(__file__).parent.parent.parent / ".cursor" / "mcp.json"

    if not config_path.exists():
        print("❌ MCP config file not found")
        return False

    try:
        with open(config_path) as f:
            config = json.load(f)

        if "mcpServers" not in config:
            print("❌ No mcpServers section in config")
            return False

        server_config = config["mcpServers"].get("unified-mcp-server")
        if not server_config:
            print("❌ unified-mcp-server not found in config")
            return False

        # Check that the command path exists
        command_path = Path(server_config["command"])
        if not command_path.exists():
            print(f"❌ Command path does not exist: {command_path}")
            return False

        print("✅ MCP configuration is valid")
        return True

    except Exception as e:
        print(f"❌ Failed to parse MCP config: {e}")
        return False


def test_environment():
    """Test that the environment is set up correctly."""
    print("🔧 Testing environment setup...")

    # Check .env file
    env_path = Path(__file__).parent / ".env"
    if not env_path.exists():
        print("❌ .env file not found")
        return False

    # Check virtual environment
    venv_path = Path(__file__).parent / ".venv"
    if not venv_path.exists():
        print("❌ Virtual environment not found")
        return False

    # Check uv executable
    uv_path = venv_path / "Scripts" / "uv.exe"
    if not uv_path.exists():
        print("❌ uv.exe not found in virtual environment")
        return False

    print("✅ Environment setup is correct")
    return True


async def main():
    """Run all tests."""
    print("🚀 Testing AiChemistForge MCP Server Setup")
    print("=" * 50)

    tests = [
        ("Environment", test_environment),
        ("MCP Config", test_mcp_config),
        ("Server Startup", test_server_startup),
    ]

    results = []
    for test_name, test_func in tests:
        if asyncio.iscoroutinefunction(test_func):
            result = await test_func()
        else:
            result = test_func()
        results.append((test_name, result))
        print()

    print("=" * 50)
    print("📋 Test Results:")
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if not result:
            all_passed = False

    if all_passed:
        print("\n🎉 All tests passed! Your MCP server should work with Cursor.")
        print("\n📝 Next steps:")
        print("  1. Restart Cursor IDE")
        print("  2. Look for the hammer 🔨 icon in Cursor")
        print(
            "  3. You should see tools: query_cursor_database, file_tree, codebase_ingest"
        )
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")

    return all_passed


if __name__ == "__main__":
    asyncio.run(main())
