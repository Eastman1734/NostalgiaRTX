@echo off
cd /d "%~dp0"
rem Use default Windows PowerShell 5.1 module paths even when started from PowerShell 7.
set "PSModulePath=%ProgramFiles%\WindowsPowerShell\Modules;%SystemRoot%\system32\WindowsPowerShell\v1.0\Modules"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\Install.ps1"
if errorlevel 1 (
  echo.
  echo Setup failed. Keep this output for diagnostics.
  pause
  exit /b 1
)
start "" "%~dp0NostalgiaRTX.exe"
