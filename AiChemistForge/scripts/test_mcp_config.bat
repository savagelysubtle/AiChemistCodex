@echo off
echo Testing MCP Server Configuration...
echo.
echo Command: D:\Coding\AiChemistCodex\AiChemistForge\ToolRack\Python\.venv\Scripts\uv.exe
echo Args: run python -m unified_mcp_server.main --transport stdio
echo Working Directory: D:\Coding\AiChemistCodex\AiChemistForge\ToolRack\Python
echo.

cd /d "D:\Coding\AiChemistCodex\AiChemistForge\ToolRack\Python"
set PYTHONPATH=src
set LOG_LEVEL=DEBUG

echo Starting MCP Server...
"D:\Coding\AiChemistCodex\AiChemistForge\ToolRack\Python\.venv\Scripts\uv.exe" run python -m unified_mcp_server.main --transport stdio