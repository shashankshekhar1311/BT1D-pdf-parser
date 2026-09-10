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

Write-Host "[148-DEV-SETUP] Ensuring repository is present at $repoRoot"
if (-not (Test-Path $repoRoot)) {
    throw "Repository not found at $repoRoot. Clone the repo first."
}

Write-Host "[148-DEV-SETUP] Pulling latest code from GitHub main"
& $gitExe -C $repoRoot pull origin main

if (-not (Test-Path (Join-Path $repoRoot ".venv"))) {
    Write-Host "[148-DEV-SETUP] Creating virtual environment"
    python -m venv (Join-Path $repoRoot ".venv")
}

Write-Host "[148-DEV-SETUP] Activating virtual environment"
. (Join-Path $repoRoot ".venv\Scripts\Activate.ps1")

Write-Host "[148-DEV-SETUP] Installing Python dependencies"
python -m pip install --upgrade pip
python -m pip install -r (Join-Path $repoRoot "requirements.txt")

Write-Host "[148-DEV-SETUP] Verifying required libraries"
python -c "import fastapi, httpx, uvicorn, torch, transformers, pymupdf, PIL; print('runtime_libs_ok')"

Write-Host "[148-DEV-SETUP] Verifying model service import path"
python -c "import os, sys; sys.path.insert(0, r'D:\pdf_parser'); import 148.app.api.model_service; print('model_import_ok')"

Write-Host "[148-DEV-SETUP] Checking if port 9001 is already in use"
$portInUse = Get-NetTCPConnection -LocalPort 9001 -ErrorAction SilentlyContinue
if ($portInUse) {
    Write-Host "[148-DEV-SETUP] Port 9001 is already occupied. You may need to stop the existing dev model service before starting the new one."
}

Write-Host "[148-DEV-SETUP] Writing runtime config for 148 development model service"
$envFile = Join-Path $repoRoot "148\config\dev.env"
@'
APP_ENV=dev
HOST=0.0.0.0
PORT=9001
RELOAD=true
MODEL_VERSION=v1_0_0
MODEL_PATH=D:/pdf_parser/148/registry/models/qwen2_5_vl/v1_0_0
MODEL_SERVICE_URL=http://127.0.0.1:9001/infer
LOOKUP_PATH=D:\pdf_parser\lookup_service.py
PYTHONPATH=D:\pdf_parser
MODEL_REGISTRY_ROOT=D:/pdf_parser/148/registry/models/qwen2_5_vl
PRODUCTION_VERSION_FILE=D:/pdf_parser/148/registry/models/qwen2_5_vl/production/current_version.txt
'@ | Set-Content -Path $envFile -Encoding utf8

Write-Host "[148-DEV-SETUP] Dev environment is ready"
Write-Host "[148-DEV-SETUP] Next step: run .\148\scripts\start_dev_148.bat"
