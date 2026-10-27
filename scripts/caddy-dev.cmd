@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0caddy_dev_shared.ps1" %1
exit /b %ERRORLEVEL%
