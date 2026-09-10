@echo off
setlocal
cd /d "%~dp0\..\.."

if not exist ".venv\Scripts\python.exe" (
    echo [148-DEV] Missing virtual environment at .venv\Scripts\python.exe
    exit /b 1
)

call ".venv\Scripts\activate.bat"
set APP_ENV=dev
set HOST=0.0.0.0
set PORT=8001
set MODEL_VERSION=dev
set MODEL_SERVICE_URL=http://127.0.0.1:9000/infer
set PYTHONPATH=%CD%

echo [148-DEV] Starting developer instance with reload enabled on port 8001...
uvicorn api:app --host %HOST% --port %PORT% --reload
