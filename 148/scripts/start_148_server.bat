@echo off
setlocal
cd /d "%~dp0\..\.."

if not exist ".venv\Scripts\python.exe" (
    echo [148-SERVER] Missing virtual environment at .venv\Scripts\python.exe
    exit /b 1
)

call ".venv\Scripts\activate.bat"

if "%MODEL_SERVER_HOST%"=="" set MODEL_SERVER_HOST=127.0.0.1
if "%MODEL_SERVER_PORT%"=="" set MODEL_SERVER_PORT=9000
if "%MODEL_SERVER_ENV%"=="" set MODEL_SERVER_ENV=prod_model

set APP_ENV=%MODEL_SERVER_ENV%
set HOST=0.0.0.0
set PORT=%MODEL_SERVER_PORT%
set RELOAD=false
set MODEL_VERSION=v1_0_0
set MODEL_PATH=%CD%\148\registry\models\qwen2_5_vl\v1_0_0
set MODEL_SERVICE_URL=http://%MODEL_SERVER_HOST%:%MODEL_SERVER_PORT%/infer
set PYTHONPATH=%CD%
set MODEL_REGISTRY_ROOT=%CD%\148\registry\models\qwen2_5_vl
set PRODUCTION_VERSION_FILE=%CD%\148\registry\models\qwen2_5_vl\production\current_version.txt

echo [148-SERVER] Starting model service on %MODEL_SERVER_HOST%:%MODEL_SERVER_PORT% with model version v1_0_0...
python "%~dp0\start_model_service_148.py"
