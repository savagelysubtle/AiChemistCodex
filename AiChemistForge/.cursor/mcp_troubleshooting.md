# MCP Server Troubleshooting Guide - Windows 11 & Cursor

## Issue Summary
Your Python MCP server runs fine in isolation but Cursor has difficulty connecting to it. This is a common issue on Windows 11 with Cursor MCP servers.

## Root Causes (Based on Cursor Forum Analysis)

### 1. **Windows Command Execution Issues**
- MCP servers on Windows need special command wrappers
- Raw executable paths don't work reliably
- Solution: Use `cmd /c` or PowerShell wrappers

### 2. **Path Resolution Problems**
- Windows path handling differs from Unix systems
- Backslashes and spaces in paths cause issues
- Virtual environment activation needs special handling

### 3. **Shell Environment Differences**
- PowerShell vs CMD execution contexts
- Environment variable inheritance issues
- PATH resolution problems

## Solutions Tested

### Configuration 1: CMD Wrapper (Recommended by Forum)
```json
{
  "mcpServers": {
    "unified-mcp-server": {
      "command": "cmd",
      "args": [
        "/c",
        "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python\\.venv\\Scripts\\uv.exe",
        "run",
        "python",
        "-m",
        "unified_mcp_server.main",
        "--transport",
        "stdio"
      ],
      "cwd": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python",
      "env": {
        "PYTHONPATH": "src",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

### Configuration 2: PowerShell Wrapper (Current)
```json
{
  "mcpServers": {
    "unified-mcp-server": {
      "command": "powershell",
      "args": [
        "-Command",
        "& 'D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python\\.venv\\Scripts\\uv.exe' run python -m unified_mcp_server.main --transport stdio"
      ],
      "cwd": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python",
      "env": {
        "PYTHONPATH": "src",
        "LOG_LEVEL": "DEBUG"
      }
    }
  }
}
```

## Server Optimizations Made

1. **Added Timeout Protection**: Server initialization now has a 5-second timeout to prevent hanging
2. **Improved Error Handling**: Better logging and graceful degradation
3. **Minimal Tool Registration**: Fallback to essential tools if full discovery fails

## Next Steps

### 1. Restart Cursor Completely
- Close all Cursor windows
- End any Cursor processes in Task Manager
- Restart Cursor
- Look for the hammer 🔨 icon in the interface

### 2. Check MCP Server Status
In Cursor:
- Go to Settings
- Look for "Features" or "MCP" section
- Check if your server appears and is active
- Try refreshing the connection

### 3. Alternative Configurations to Try

#### Option A: Direct Python Call
```json
{
  "command": "python",
  "args": ["-m", "unified_mcp_server.main", "--transport", "stdio"],
  "cwd": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python\\src",
  "env": {
    "PATH": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python\\.venv\\Scripts;%PATH%",
    "PYTHONPATH": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python\\src"
  }
}
```

#### Option B: Batch Script Wrapper
Create `start_mcp.bat`:
```batch
@echo off
cd /d "D:\Coding\AiChemistCodex\AiChemistForge\ToolRack\Python"
.venv\Scripts\uv.exe run python -m unified_mcp_server.main --transport stdio
```

Then use:
```json
{
  "command": "D:\\Coding\\AiChemistCodex\\AiChemistForge\\ToolRack\\Python\\start_mcp.bat"
}
```

## Debugging Commands

```bash
# Test server manually
cd ToolRack\Python
uv run python -m unified_mcp_server.main --transport stdio

# Run debug script
python debug_server.py

# Test configuration
python test_mcp_server.py
```

## Expected Tools
When working, you should see these tools in Cursor:
- `query_cursor_database` - Query Cursor IDE databases
- `file_tree` - Generate directory structures
- `codebase_ingest` - Process entire codebases
- `manage_plugins` - Plugin management

## Forum References
- [Cursor MCP server don't work](https://forum.cursor.com/t/cursor-mcp-server-dont-work/71063)
- [MCP Feature "Client Closed" Fix](https://forum.cursor.com/t/mcp-feature-client-closed-fix/54651)

Key insight: Use `cmd /c` wrapper for Windows batch scripts and executables.