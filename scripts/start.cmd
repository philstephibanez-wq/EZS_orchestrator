@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0v2_lifecycle.ps1" start
exit /b %ERRORLEVEL%
