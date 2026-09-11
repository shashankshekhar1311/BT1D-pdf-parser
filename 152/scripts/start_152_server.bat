@echo off
setlocal enabledelayedexpansion

set "REPO_ROOT=%~dp0\..\.."
pushd "%REPO_ROOT%" || exit /b 1

set "VENV_PYTHON=%REPO_ROOT%\.venv\Scripts\python.exe"

if not exist "%VENV_PYTHON%" (
    echo [152-SERVER] Missing virtual environment at %VENV_PYTHON%
    exit /b 1
)

if "%MODEL_SERVICE_HOST%"=="" set "MODEL_SERVICE_HOST=10.0.0.148"
if "%MODEL_SERVICE_PORT%"=="" set "MODEL_SERVICE_PORT=9000"
if "%GATEWAY_ENV%"=="" set "GATEWAY_ENV=prod"
if "%GATEWAY_PORT%"=="" set "GATEWAY_PORT=8000"

rem Kill stale listeners already using the configured gateway port.
for /f "tokens=5" %%P in ('netstat -ano ^| findstr /R /C:":%GATEWAY_PORT% " 2^>nul') do (
    if not "%%P"=="" (
        echo [152-SERVER] Found stale process on port %GATEWAY_PORT% (PID %%P). Stopping it.
        taskkill /PID %%P /F >nul 2>&1
    )
)

timeout /t 2 >nul
netstat -ano | findstr /R /C:":%GATEWAY_PORT% " >nul
if not errorlevel 1 (
    echo [152-SERVER] Port %GATEWAY_PORT% is still in use after cleanup. Close the active process and retry.
    exit /b 1
)

set "APP_ENV=%GATEWAY_ENV%"
set "HOST=0.0.0.0"
set "PORT=%GATEWAY_PORT%"
set "RELOAD=false"
set "MODEL_VERSION=v1_0_0"
set "MODEL_PATH=%CD%\148\registry\models\qwen2_5_vl\v1_0_0"
set "MODEL_SERVICE_URL=http://%MODEL_SERVICE_HOST%:%MODEL_SERVICE_PORT%/infer"
set "PYTHONPATH=%CD%"
set "INTERNAL_MODEL_HOST=%MODEL_SERVICE_HOST%"
set "INTERNAL_MODEL_PORT=%MODEL_SERVICE_PORT%"
set "INTERNAL_MODEL_ENDPOINT=/infer"

echo [152-SERVER] Starting gateway on port %GATEWAY_PORT% targeting model service at http://%MODEL_SERVICE_HOST%:%MODEL_SERVICE_PORT%/infer...
"%VENV_PYTHON%" "%~dp0start_gateway_152.py"
