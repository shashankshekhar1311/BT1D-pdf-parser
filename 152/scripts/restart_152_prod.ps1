$ErrorActionPreference = "Stop"

Write-Host "[152-RESTART] Cleaning stale listeners on ports 8000 and 9000"

$ports = @(8000, 9000)
foreach ($port in $ports) {
    $p = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($p) {
        Stop-Process -Id $p -Force
        Write-Host "[152-RESTART] Stopped process $p on port $port"
    }
}

Write-Host "[152-RESTART] Starting production gateway on port 8000"
Set-Location "D:\pdf_parser"
. ".\.venv\Scripts\Activate.ps1"
.
.\152\scripts\start_152_server.bat

Write-Host "[152-RESTART] Verifying gateway health"
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing
