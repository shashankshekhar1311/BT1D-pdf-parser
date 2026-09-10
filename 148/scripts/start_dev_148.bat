@echo off
setlocal
cd /d "%~dp0\..\.."

if not exist ".venv\Scripts\python.exe" (
    echo [148-DEV] Virtual environment not found at .venv\Scripts\python.exe
    echo [148-DEV] Please create or activate the project virtual environment first.
    exit /b 1
)

call ".venv\Scripts\activate.bat"
set APP_ENV=dev
set HOST=0.0.0.0
set PORT=9001
set RELOAD=true
set MODEL_VERSION=dev
set MODEL_SERVICE_URL=http://127.0.0.1:9001/infer
set PYTHONPATH=%CD%

echo [148-DEV] Starting development model service on port 9001...
python "%~dp0\start_model_service_148.py"
