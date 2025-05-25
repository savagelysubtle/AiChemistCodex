#!/usr/bin/env python3
"""Test script to verify the MCP server is working."""

import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import pytest


@pytest.mark.asyncio
async def test_server_startup():
    """Test that the MCP server starts up correctly."""
    print("Testing MCP Server startup...")

    # Get the path to the project root
    project_root = Path(__file__).parent.parent

    process: Optional[subprocess.Popen] = None

    try:
        # Start the server process using the proper module path
        print("Starting server: python -m unified_mcp_server.main --transport stdio")

        process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "unified_mcp_server.main",
                "--transport",
                "stdio",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=project_root,
        )

        # Give the server a moment to start
        time.sleep(3)

        # Check if process is still running (this indicates successful startup)
        if process.poll() is None:
            print("✅ Server started successfully and is running")

            # Terminate the server
            process.terminate()

            # Wait for clean shutdown
            try:
                process.wait(timeout=5)
                print("✅ Server terminated cleanly")
            except subprocess.TimeoutExpired:
                print("⚠️ Server didn't terminate gracefully, forcing...")
                process.kill()
                process.wait()

            # Assert success
            assert True, "Server should start and terminate successfully"

        else:
            # Process exited unexpectedly
            stdout, stderr = process.communicate()
            error_msg = f"Server exited unexpectedly with code: {process.returncode}"
            if stdout:
                error_msg += f"\nStdout: {stdout}"
            if stderr:
                error_msg += f"\nStderr: {stderr}"

            pytest.fail(error_msg)

    except Exception as e:
        # Clean up process if it exists
        if process is not None:
            try:
                process.terminate()
                process.wait(timeout=2)
            except (subprocess.TimeoutExpired, OSError):
                try:
                    process.kill()
                    process.wait()
                except:
                    pass
        pytest.fail(f"Error testing server: {e}")


@pytest.mark.asyncio
async def test_server_module_import():
    """Test that the server module can be imported without errors."""
    print("Testing server module import...")

    try:
        # Try to import the main module
        from unified_mcp_server import main

        print("✅ Server module imported successfully")

        # Check that the main function exists
        assert hasattr(main, "main"), "main function should exist"
        print("✅ Main function found")

    except ImportError as e:
        pytest.fail(f"Failed to import server module: {e}")


# For backwards compatibility, keep the original function
def test_server():
    """Legacy test function for direct execution."""
    import asyncio

    try:
        asyncio.run(test_server_startup())
        print("✅ Server test completed successfully")
    except Exception as e:
        print(f"❌ Error testing server: {e}")
        pytest.fail(f"Server test failed: {e}")


if __name__ == "__main__":
    test_server()
