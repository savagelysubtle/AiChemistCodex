# Check for MCP logs in Cursor
Write-Host "Checking for Cursor MCP logs..." -ForegroundColor Green

$logsPath = "$env:APPDATA\Cursor\logs"
$latestSession = Get-ChildItem $logsPath -Directory | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if ($latestSession) {
    Write-Host "Latest session: $($latestSession.Name)" -ForegroundColor Yellow

    # Look for MCP logs
    $mcpLogs = Get-ChildItem $latestSession.FullName -Recurse -Filter "*MCP*" -ErrorAction SilentlyContinue

    if ($mcpLogs) {
        Write-Host "Found MCP logs:" -ForegroundColor Green
        $mcpLogs | ForEach-Object { Write-Host "  - $($_.FullName)" }

        # Show last few lines of the most recent MCP log
        $latestMcpLog = $mcpLogs | Sort-Object LastWriteTime -Descending | Select-Object -First 1
        Write-Host "`nLast 10 lines of MCP log:" -ForegroundColor Cyan
        Get-Content $latestMcpLog.FullName -Tail 10 -ErrorAction SilentlyContinue
    }
    else {
        Write-Host "No MCP logs found. Cursor may not have tried to connect yet." -ForegroundColor Red
        Write-Host "Make sure to restart Cursor completely and try using MCP features." -ForegroundColor Yellow
    }
}
else {
    Write-Host "No Cursor session logs found." -ForegroundColor Red
}