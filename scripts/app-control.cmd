@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0app-control.ps1" -Application %1 -Action %2
exit /b %ERRORLEVEL%
