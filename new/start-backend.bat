@echo off
setlocal
TITLE SAU Backend Only Starter

REM Configure the Conda environment name used by the backend.
SET "CONDA_ENV_NAME=social-auto-upload"

where conda >nul 2>&1
IF ERRORLEVEL 1 (
    ECHO [ERROR] Could not find "conda" on PATH.
    ECHO Please open "Anaconda Prompt" or add Conda to PATH, then rerun this script.
    GOTO :END
)

ECHO ==================================================
ECHO   Starting social-auto-upload Backend Only...
ECHO ==================================================
ECHO.

ECHO Using Conda environment: %CONDA_ENV_NAME%
ECHO [1/1] Starting Python Backend Server in a new window...
START "SAU Backend" cmd /k "call conda activate %CONDA_ENV_NAME% && python sau_backend.py"

ECHO.
ECHO Backend window launched. Monitor logs there and press Ctrl+C to stop.
ECHO This launcher will close in 5 seconds...
timeout /t 5 /nobreak > nul

:END
endlocal
