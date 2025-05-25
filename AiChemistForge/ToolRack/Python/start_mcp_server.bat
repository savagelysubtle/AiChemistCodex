@echo off
REM AiChemistForge MCP Server Launcher
REM This script makes it easier for other projects to connect to the server
REM Follows 1000-mcp-stdio-logging.mdc guidelines for local MCP server development

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"

REM Change to the project directory
cd /d "%PROJECT_ROOT%"

REM Check if virtual environment exists
if not exist ".venv\Scripts\uv.exe" (
    echo Error: Virtual environment not found at %PROJECT_ROOT%\.venv >&2
    echo Please run 'uv sync --all-groups' first >&2
    exit /b 1
)

REM Set environment variables for MCP operation
set "PYTHONPATH=src"
set "LOG_LEVEL=INFO"

REM Check for debug flag
set "DEBUG_FLAG="
if "%1"=="--debug" (
    set "DEBUG_FLAG=--debug"
    echo Debug mode enabled - detailed logging will appear on stderr >&2
)

REM Display startup message (to stderr to avoid JSON-RPC interference)
echo Starting AiChemistForge MCP Server with stdio transport... >&2
echo Logs will appear on stderr, JSON-RPC communication on stdout >&2

REM Start the MCP server with stdio transport (default per MCP guidelines)
REM Per 1000-mcp-stdio-logging.mdc: prioritize stdio for local MCP servers
".venv\Scripts\uv.exe" run python -m unified_mcp_server.main --stdio %DEBUG_FLAG%