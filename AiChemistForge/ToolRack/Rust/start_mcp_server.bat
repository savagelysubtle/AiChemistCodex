@echo off
REM AiChemistForge Rust MCP Server Launcher
REM This script sets up the Rust environment and starts the MCP server
REM Follows MCP best practices for local development

setlocal enabledelayedexpansion

REM Get the directory where this script is located
set "SCRIPT_DIR=%~dp0"
set "PROJECT_ROOT=%SCRIPT_DIR%"

REM Change to the project directory
cd /d "%PROJECT_ROOT%"

REM Set up Rust environment
set "RUST_LOG=debug"

REM Check for debug flag
set "DEBUG_FLAG="
if "%1"=="--debug" (
    set "DEBUG_FLAG=--debug"
    echo Debug mode enabled - detailed logging will appear on stderr >&2
)

REM Display startup message (to stderr to avoid JSON-RPC interference)
echo Starting AiChemistForge Rust MCP Server with stdio transport... >&2
echo Logs will appear on stderr, JSON-RPC communication on stdout >&2

REM Set default Rust toolchain if not already set
rustup default stable >nul 2>&1

REM Start the Rust MCP server with filesystem tools
REM Arguments: --allow-write for write permissions, followed by allowed directories
cargo run -- --allow-write "%PROJECT_ROOT%test_files" F:\ D:\