@echo off
powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File "%~dp0stop.ps1"
exit /b %ERRORLEVEL%
