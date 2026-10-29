@echo off
cd /d "%~dp0"
if not exist "%~dp0.runtime\python.exe" (
  call "%~dp0INSTALL.cmd"
  exit /b
)
"%~dp0.runtime\python.exe" "%~dp0main.py"
if errorlevel 1 pause
