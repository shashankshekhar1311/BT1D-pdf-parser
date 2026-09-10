$ErrorActionPreference = "Stop"

$repoRoot = "D:\pdf_parser"
Set-Location $repoRoot

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

Write-Host "[152-SETUP] Ensuring repository is present at $repoRoot"
if (-not (Test-Path $repoRoot)) {
    throw "Repository not found at $repoRoot. Clone the repo first."
}

# Ensure GitHub code is the source of truth
Write-Host "[152-SETUP] Pulling latest code from GitHub main"
& $gitExe -C $repoRoot pull origin main

# Create virtual environment if missing
if (-not (Test-Path (Join-Path $repoRoot ".venv"))) {
    Write-Host "[152-SETUP] Creating virtual environment"
    python -m venv (Join-Path $repoRoot ".venv")
}

# Activate the venv
Write-Host "[152-SETUP] Activating virtual environment"
. (Join-Path $repoRoot ".venv\Scripts\Activate.ps1")

# Upgrade pip and install project dependencies
Write-Host "[152-SETUP] Installing Python dependencies"
python -m pip install --upgrade pip
python -m pip install -r (Join-Path $repoRoot "requirements.txt")

# Validate required runtime packages
Write-Host "[152-SETUP] Verifying required libraries"
python -c "import fastapi, httpx, uvicorn, pydantic; print('runtime_libs_ok')"

# Ensure the repo root is importable
Write-Host "[152-SETUP] Verifying gateway import path"
python -c "import os, sys; sys.path.insert(0, r'D:\pdf_parser'); import 152.app.api.gateway; print('gateway_import_ok')"

# Check for a stale port listener before startup
Write-Host "[152-SETUP] Checking if port 8000 is already in use"
$portInUse = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "[152-SETUP] Port 8000 is already occupied. You may need to stop the old gateway before starting the new one."
}

# Configure env values for 152 gateway
Write-Host "[152-SETUP] Writing runtime config for 152 gateway"
$envFile = Join-Path $repoRoot "152\config\prod.env"
@'
APP_ENV=prod
HOST=0.0.0.0
PORT=8000
RELOAD=false
MODEL_SERVICE_URL=http://127.0.0.1:9000/infer
MODEL_VERSION=v1_0_0
MODEL_PATH=D:/pdf_parser/148/registry/models/qwen2_5_vl/v1_0_0
INPUT_MODE=batch
OUTPUT_MODE=combined_json
PYTHONPATH=D:\pdf_parser
INTERNAL_MODEL_HOST=127.0.0.1
INTERNAL_MODEL_PORT=9000
INTERNAL_MODEL_ENDPOINT=/infer
'@ | Set-Content -Path $envFile -Encoding utf8

# Show final status
Write-Host "[152-SETUP] 152 environment is ready"
Write-Host "[152-SETUP] Next step: run .\152\scripts\start_152_server.bat"
