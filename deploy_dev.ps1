$ErrorActionPreference = "Stop"

Write-Host "[DEPLOY-DEV] Starting local development deployment"
Set-Location "D:\pdf_parser"

# 1. Pull latest GitHub code
Write-Host "[DEPLOY-DEV] Pulling latest code from GitHub main"
git -C "D:\pdf_parser" pull origin main

# 2. Ensure both local dev environments are configured
Write-Host "[DEPLOY-DEV] Setting up 148 dev environment"
. "D:\pdf_parser\148\scripts\setup_148_dev.ps1"

Write-Host "[DEPLOY-DEV] Setting up 152 dev environment"
. "D:\pdf_parser\152\scripts\setup_152_dev.ps1"

# 3. Clean stale dev listeners to avoid port conflicts
Write-Host "[DEPLOY-DEV] Cleaning stale local dev listeners"
$ports = @(8001, 9001)
foreach ($port in $ports) {
    $p = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($p) {
        Stop-Process -Id $p -Force
        Write-Host "[DEPLOY-DEV] Stopped process $p on port $port"
    }
}

# 4. Start 148 model service
Write-Host "[DEPLOY-DEV] Starting 148 dev model service"
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'Set-Location D:\pdf_parser; .\.venv\Scripts\Activate.ps1; .\148\scripts\start_dev_148.bat'

# 5. Wait for inference service to initialize
Start-Sleep -Seconds 12

# 6. Start 152 gateway
Write-Host "[DEPLOY-DEV] Starting 152 dev gateway"
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'Set-Location D:\pdf_parser; .\.venv\Scripts\Activate.ps1; .\152\scripts\start_dev_152.bat'

# 7. Validate health
Write-Host "[DEPLOY-DEV] Validating dev model and gateway health"
Invoke-WebRequest -Uri "http://127.0.0.1:9001/health" -UseBasicParsing
Invoke-WebRequest -Uri "http://127.0.0.1:8001/health" -UseBasicParsing

Write-Host "[DEPLOY-DEV] Local development deployment complete"
