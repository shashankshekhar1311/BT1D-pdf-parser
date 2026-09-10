@echo off
setlocal
cd /d "%~dp0\..\.."

if not exist ".venv\Scripts\python.exe" (
    echo [152-DEV] Missing virtual environment at .venv\Scripts\python.exe
    exit /b 1
)

call ".venv\Scripts\activate.bat"
set APP_ENV=dev
set HOST=0.0.0.0
set PORT=8001
set RELOAD=true
set MODEL_VERSION=dev
set MODEL_SERVICE_URL=http://127.0.0.1:9001/infer
set PYTHONPATH=%CD%

echo [152-DEV] Starting development gateway on port 8001 pointing to model service 9001...
python "%~dp0\start_gateway_152.py"
