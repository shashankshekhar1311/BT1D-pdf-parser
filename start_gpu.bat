@echo off
setlocal

set "REPO_ROOT=%~dp0"
set "PORT=8000"
set "VENV_DIR=%REPO_ROOT%.venv"

:parse_args
if "%~1"=="" goto start
if /I "%~1"=="--port" (
    set "PORT=%~2"
    shift
    shift
    goto parse_args
)
if /I "%~1"=="--help" goto help
if /I "%~1"=="-h" goto help
shift
goto parse_args

:help
echo Usage: start_gpu.bat [--port 8000]
echo Example: start_gpu.bat
echo Example: start_gpu.bat --port 8000
exit /b 0

:start
call :rebuild_venv
call :activate_venv
call :install_cuda_torch
call :install_requirements
call :verify_cuda
call :start_api
exit /b 0

:rebuild_venv
if exist "%VENV_DIR%" (
    echo Removing old virtual environment: %VENV_DIR%
    rmdir /s /q "%VENV_DIR%"
)

echo Creating fresh virtual environment at %VENV_DIR%
python -m venv "%VENV_DIR%"
if errorlevel 1 (
    echo Failed to create virtual environment.
    exit /b 1
)
exit /b 0

:activate_venv
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo Failed to activate virtual environment.
    exit /b 1
)
exit /b 0

:install_cuda_torch
echo Installing CUDA-enabled PyTorch and torchvision for Windows...
python -m pip install --upgrade pip setuptools wheel
python -m pip install --index-url https://download.pytorch.org/whl/cu121 torch==2.5.1 torchvision==0.20.1
if errorlevel 1 (
    echo Failed to install CUDA-enabled PyTorch packages.
    exit /b 1
)
exit /b 0

:install_requirements
if exist "%REPO_ROOT%requirements.txt" (
    echo Installing project dependencies...
    python -m pip install -r "%REPO_ROOT%requirements.txt"
    if errorlevel 1 (
        echo Failed to install requirements.
        exit /b 1
    )
) else (
    echo requirements.txt not found in %REPO_ROOT%
    exit /b 1
)
exit /b 0

:verify_cuda
python -c "import torch; print('CUDA_AVAILABLE=' + str(torch.cuda.is_available())); print('CUDA_VERSION=' + str(torch.version.cuda)); print('GPU_COUNT=' + str(torch.cuda.device_count()))"
if errorlevel 1 (
    echo CUDA verification failed.
    exit /b 1
)
python -c "import torch; raise SystemExit(0 if torch.cuda.is_available() and torch.cuda.device_count() > 0 else 1)"
if errorlevel 1 (
    echo.
    echo CUDA is still unavailable in this environment.
    echo This machine must have an NVIDIA GPU with the proper driver and CUDA runtime installed.
    exit /b 1
)
exit /b 0

:start_api
cd /d "%REPO_ROOT%"
echo Starting API on port %PORT% with GPU-enabled environment...
uvicorn api:app --host 0.0.0.0 --port %PORT% --reload
exit /b 0
