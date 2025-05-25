#!/usr/bin/env python3
"""Test MCP server connection and functionality."""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent / "src"))


async def test_mcp_server():
    """Test the MCP server via subprocess to simulate Cursor's connection."""
    print("🧪 Testing MCP Server Connection...")

    process = None
    try:
        # Start the server process
        process = subprocess.Popen(
            [
                ".venv/Scripts/uv.exe",
                "run",
                "python",
                "-m",
                "unified_mcp_server.main",
                "--stdio",
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent,
        )

        # Send MCP initialization request
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
        request_json = json.dumps(init_request) + "\n"
        if process.stdin:
            process.stdin.write(request_json)
            process.stdin.flush()

        # Read response with timeout
        try:
            stdout, stderr = process.communicate(timeout=5)

            if stderr:
                print(f"❌ Server stderr: {stderr}")
                return False

            if stdout:
                print("✅ Server response received")
                print(f"Response preview: {stdout[:200]}...")

                # Try to parse as JSON
                try:
                    lines = stdout.strip().split("\n")
                    for line in lines:
                        if line.strip():
                            response = json.loads(line)
                            if response.get("id") == 1:
                                print("✅ Valid JSON-RPC response received")
                                return True
                except json.JSONDecodeError as e:
                    print(f"❌ Invalid JSON response: {e}")
                    print(f"Raw output: {stdout}")
                    return False
            else:
                print("❌ No response from server")
                return False

        except subprocess.TimeoutExpired:
            print("❌ Server response timeout")
            if process:
                process.kill()
            return False

    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

    finally:
        if process and process.poll() is None:
            process.terminate()


if __name__ == "__main__":
    success = asyncio.run(test_mcp_server())
    if success:
        print("\n🎉 MCP Server test passed! Server should work with Cursor.")
    else:
        print("\n❌ MCP Server test failed. Check the issues above.")
    sys.exit(0 if success else 1)
