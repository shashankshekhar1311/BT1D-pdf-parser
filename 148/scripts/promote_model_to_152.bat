@echo off
setlocal
set MODEL_ROOT=D:\pdf_parser\148\registry\models\qwen2_5_vl
set PROD_ROOT=%MODEL_ROOT%\production
set CURRENT_VERSION_FILE=%PROD_ROOT%\current_version.txt

if not exist "%CURRENT_VERSION_FILE%" (
    echo [PROMOTE] No approved version found in %PROD_ROOT%
    exit /b 1
)

set /p CURRENT_VERSION=<"%CURRENT_VERSION_FILE%"

echo [PROMOTE] Approved version is %CURRENT_VERSION%

echo [PROMOTE] This version is now the approved internal model for 152.

echo [PROMOTE] Update 152 config to point to %MODEL_ROOT%\%CURRENT_VERSION% when the production gateway is deployed.
