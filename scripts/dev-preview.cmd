@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0ezscore_dev_preview.ps1" %1
exit /b %ERRORLEVEL%
