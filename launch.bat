@echo off
setlocal
cd /d "%~dp0"

if not exist "logs" mkdir "logs"

start "" /b powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden ^
  -File "%~dp0scripts\launch_hidden.ps1"

exit /b 0
