@echo off
setlocal enableextensions
TITLE SAU One-Click Start

REM Resolve script directory
set "ROOT=%~dp0"
pushd "%ROOT%" >nul

for %%P in (5406 5106) do (
  for /f "tokens=5" %%T in ('netstat -aon ^| findstr :%%P ^| findstr LISTENING') do (
    taskkill /F /PID %%T >nul 2>&1
  )
)

echo ==================================================
echo  Starting social-auto-upload (Backend + Frontend)
echo ==================================================
echo.

REM Start Backend in new window using local venv
if exist ".venv\Scripts\python.exe" (
  start "SAU Backend" /D "%ROOT%" cmd /k ".\.venv\Scripts\python.exe sau_backend.py"
) else (
  start "SAU Backend" /D "%ROOT%" cmd /k "python sau_backend.py"
)

REM Start Frontend in new window, install deps if missing, fixed to 5106
echo [2/2] Starting Frontend on port 5106...
set "FE_DIR=%ROOT%sau_frontend"
if exist "%FE_DIR%\node_modules" (
  start "SAU Frontend" /D "%FE_DIR%" cmd /k "npx vite --host 0.0.0.0 --port 5106 --strictPort"
) else (
  start "SAU Frontend" /D "%FE_DIR%" cmd /k "npm install && npx vite --host 0.0.0.0 --port 5106 --strictPort"
)

echo.
echo ==================================================
echo  Two windows opened: Backend and Frontend
echo  Backend: http://localhost:5406
echo  Frontend: http://localhost:5106
echo ==================================================
echo.

popd >nul
exit /b 0
