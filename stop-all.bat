@echo off
setlocal enableextensions
set "ROOT=%~dp0"
pushd "%ROOT%" >nul

set PORTS=5406 5106
for %%P in (%PORTS%) do (
  for /f "tokens=5" %%T in ('netstat -aon ^| findstr :%%P ^| findstr LISTENING') do (
    taskkill /F /PID %%T >nul 2>&1
  )
)

popd >nul
exit /b 0

