$ErrorActionPreference = "Stop"

Write-Host "[148-DEV-RESTART] Cleaning stale listeners on port 9001"

$ports = @(9001)
foreach ($port in $ports) {
    $p = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($p) {
        Stop-Process -Id $p -Force
        Write-Host "[148-DEV-RESTART] Stopped process $p on port $port"
    }
}

Write-Host "[148-DEV-RESTART] Starting development model service on port 9001"
Set-Location "D:\pdf_parser"
. ".\.venv\Scripts\Activate.ps1"
.\148\scripts\start_dev_148.bat

Write-Host "[148-DEV-RESTART] Verifying model health"
Invoke-WebRequest -Uri "http://127.0.0.1:9001/health" -UseBasicParsing
