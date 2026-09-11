$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..")).Path
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"
$gatewayScript = Join-Path $PSScriptRoot "start_gateway_152.py"

Set-Location $repoRoot

if (-not (Test-Path $venvPython)) {
    throw "[152-SERVER] Missing virtual environment at $venvPython"
}

$modelServiceHost = if ($env:MODEL_SERVICE_HOST) { $env:MODEL_SERVICE_HOST } else { "10.0.0.148" }
$modelServicePort = if ($env:MODEL_SERVICE_PORT) { $env:MODEL_SERVICE_PORT } else { "9000" }
$gatewayEnv = if ($env:GATEWAY_ENV) { $env:GATEWAY_ENV } else { "prod" }
$gatewayPort = if ($env:GATEWAY_PORT) { $env:GATEWAY_PORT } else { "8000" }

Write-Host "[152-SERVER] Cleaning stale listeners on port $gatewayPort"
$stale = Get-NetTCPConnection -LocalPort ([int]$gatewayPort) -ErrorAction SilentlyContinue
if ($stale) {
    foreach ($entry in $stale) {
        $procId = $entry.OwningProcess
        if ($procId) {
            Write-Host "[152-SERVER] Found stale process on port $gatewayPort (PID $procId). Stopping it."
            Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        }
    }
    Start-Sleep -Seconds 2
}

$stillListening = Get-NetTCPConnection -LocalPort ([int]$gatewayPort) -ErrorAction SilentlyContinue
if ($stillListening) {
    throw "[152-SERVER] Port $gatewayPort is still in use after cleanup. Close the active process and retry."
}

$env:APP_ENV = $gatewayEnv
$env:HOST = "0.0.0.0"
$env:PORT = $gatewayPort
$env:RELOAD = "false"
$env:MODEL_VERSION = "v1_0_0"
$env:MODEL_PATH = (Join-Path $repoRoot "148\registry\models\qwen2_5_vl\v1_0_0")
$env:MODEL_SERVICE_URL = "http://${modelServiceHost}:${modelServicePort}/infer"
$env:PYTHONPATH = $repoRoot
$env:INTERNAL_MODEL_HOST = $modelServiceHost
$env:INTERNAL_MODEL_PORT = $modelServicePort
$env:INTERNAL_MODEL_ENDPOINT = "/infer"

Write-Host "[152-SERVER] Starting gateway on port $gatewayPort targeting model service at $($env:MODEL_SERVICE_URL)"
& $venvPython $gatewayScript
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
