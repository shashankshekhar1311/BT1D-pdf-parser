@echo off
setlocal
cd /d "%~dp0\..\.."

if not exist ".venv\Scripts\python.exe" (
    echo [148] Missing virtual environment at .venv\Scripts\python.exe
    exit /b 1
)

call ".venv\Scripts\activate.bat"
set APP_ENV=prod_model
set HOST=0.0.0.0
set PORT=9000
set RELOAD=false
set MODEL_VERSION=v1_0_0
set MODEL_SERVICE_URL=http://127.0.0.1:9000/infer
set MODEL_REGISTRY_ROOT=D:\pdf_parser\148\registry\models\qwen2_5_vl
set PRODUCTION_VERSION_FILE=D:\pdf_parser\148\registry\models\qwen2_5_vl\production\current_version.txt
set PYTHONPATH=%CD%

echo [148] Starting approved model service on port 9000...
python "%~dp0\start_model_service_148.py"
