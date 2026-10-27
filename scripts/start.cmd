@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0v2_lifecycle.ps1" start
if errorlevel 1 exit /b %ERRORLEVEL%
"H:\Python\pythoncore-3.14-64\python.exe" "%~dp0prod-edge-start.py"
exit /b %ERRORLEVEL%
