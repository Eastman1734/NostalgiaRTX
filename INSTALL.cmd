@echo off
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Install.ps1"
if errorlevel 1 (
  echo.
  echo Setup failed. Keep this output for diagnostics.
  pause
  exit /b 1
)
start "" "%~dp0NostalgiaRTX.exe"
