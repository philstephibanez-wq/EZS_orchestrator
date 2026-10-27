@echo off
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0v2_lifecycle.ps1" -Action status
exit /b %ERRORLEVEL%
