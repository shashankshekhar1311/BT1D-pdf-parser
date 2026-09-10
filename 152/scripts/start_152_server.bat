@echo off
setlocal
cd /d "%~dp0\..\.."

if not exist ".venv\Scripts\python.exe" (
    echo [152-SERVER] Missing virtual environment at .venv\Scripts\python.exe
    exit /b 1
)

call ".venv\Scripts\activate.bat"

if "%MODEL_SERVICE_HOST%"=="" set MODEL_SERVICE_HOST=127.0.0.1
if "%MODEL_SERVICE_PORT%"=="" set MODEL_SERVICE_PORT=9000
if "%GATEWAY_ENV%"=="" set GATEWAY_ENV=prod
if "%GATEWAY_PORT%"=="" set GATEWAY_PORT=8000

set APP_ENV=%GATEWAY_ENV%
set HOST=0.0.0.0
set PORT=%GATEWAY_PORT%
set RELOAD=false
set MODEL_VERSION=v1_0_0
set MODEL_PATH=%CD%\148\registry\models\qwen2_5_vl\v1_0_0
set MODEL_SERVICE_URL=http://%MODEL_SERVICE_HOST%:%MODEL_SERVICE_PORT%/infer
set PYTHONPATH=%CD%
set INTERNAL_MODEL_HOST=%MODEL_SERVICE_HOST%
set INTERNAL_MODEL_PORT=%MODEL_SERVICE_PORT%
set INTERNAL_MODEL_ENDPOINT=/infer

echo [152-SERVER] Starting gateway on port %GATEWAY_PORT% targeting model service at http://%MODEL_SERVICE_HOST%:%MODEL_SERVICE_PORT%/infer...
python "%~dp0\start_gateway_152.py"
