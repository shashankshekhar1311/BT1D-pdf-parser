$ErrorActionPreference = "Stop"

Write-Host "[DEPLOY] Starting production deployment"
Set-Location "D:\pdf_parser"

$gitExe = (Get-Command git -ErrorAction SilentlyContinue).Source
if (-not $gitExe) {
    $possibleGitPaths = @(
        "D:\Git\cmd\git.exe",
        "C:\Program Files\Git\cmd\git.exe",
        "C:\Program Files\Git\bin\git.exe"
    )
    foreach ($candidate in $possibleGitPaths) {
        if (Test-Path $candidate) {
            $gitExe = $candidate
            break
        }
    }
}
if (-not $gitExe) {
    throw "Git was not found on PATH and no standard install location was detected. Install Git for Windows and retry."
}

# 1. Pull latest GitHub code
Write-Host "[DEPLOY] Pulling latest code from GitHub main"
& $gitExe -C "D:\pdf_parser" pull origin main

# 2. Ensure both virtual environments exist and dependencies are installed
Write-Host "[DEPLOY] Setting up 148 model server environment"
. "D:\pdf_parser\148\scripts\setup_148_server.ps1"

Write-Host "[DEPLOY] Setting up 152 gateway environment"
. "D:\pdf_parser\152\scripts\setup_152_server.ps1"

# 3. Clean stale listeners to avoid port conflicts
Write-Host "[DEPLOY] Cleaning stale listeners"
$ports = @(8000, 9000)
foreach ($port in $ports) {
    $p = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    if ($p) {
        Stop-Process -Id $p -Force
        Write-Host "[DEPLOY] Stopped process $p on port $port"
    }
}

# 4. Start 148 model service
Write-Host "[DEPLOY] Starting 148 model service"
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'Set-Location D:\pdf_parser; .\.venv\Scripts\Activate.ps1; .\148\scripts\start_148_server.bat'

# 5. Wait for inference service to initialize
Start-Sleep -Seconds 12

# 6. Start 152 gateway
Write-Host "[DEPLOY] Starting 152 gateway"
Start-Process powershell -ArgumentList '-NoExit', '-Command', 'Set-Location D:\pdf_parser; .\.venv\Scripts\Activate.ps1; .\152\scripts\start_152_server.bat'

# 7. Validate health
Write-Host "[DEPLOY] Validating model and gateway health"
Invoke-WebRequest -Uri "http://127.0.0.1:9000/health" -UseBasicParsing
Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -UseBasicParsing

Write-Host "[DEPLOY] Production deployment complete"
