$ErrorActionPreference = "Stop"

Write-Host "[152-DEV-RESTART] Cleaning stale listeners on ports 8001 and 9001"

$ports = @(8001, 9001)
foreach ($port in $ports) {
    $p = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($p) {
        Stop-Process -Id $p -Force
        Write-Host "[152-DEV-RESTART] Stopped process $p on port $port"
    }
}

Write-Host "[152-DEV-RESTART] Starting development model service on port 9001"
Set-Location "D:\pdf_parser"
. ".\.venv\Scripts\Activate.ps1"
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'Set-Location D:\pdf_parser; .\.venv\Scripts\Activate.ps1; .\148\scripts\start_dev_148.bat'

Start-Sleep -Seconds 8

Write-Host "[152-DEV-RESTART] Starting development gateway on port 8001"
.\152\scripts\start_dev_152.bat

Write-Host "[152-DEV-RESTART] Verifying dev model and gateway health"
Invoke-WebRequest -Uri "http://127.0.0.1:9001/health" -UseBasicParsing
Invoke-WebRequest -Uri "http://127.0.0.1:8001/health" -UseBasicParsing
