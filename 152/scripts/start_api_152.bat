@echo off
setlocal
cd /d "%~dp0\..\.."

if not exist ".venv\Scripts\python.exe" (
    echo [152] Virtual environment not found at .venv\Scripts\python.exe
    echo [152] Use the 152 project environment or sync dependencies before starting.
    exit /b 1
)

call ".venv\Scripts\activate.bat"
set APP_ENV=prod
set HOST=0.0.0.0
set PORT=8000
set RELOAD=false
set MODEL_VERSION=v1_0_0
set MODEL_SERVICE_URL=http://127.0.0.1:9000/infer
set PYTHONPATH=%CD%

echo [152] Starting production API gateway on port 8000...
python "%~dp0\start_gateway_152.py"
