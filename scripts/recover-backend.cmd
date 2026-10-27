@echo off
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0v2_lifecycle.ps1" -Action recover -ExpectedPid %1 -ConfirmRecovery
exit /b %ERRORLEVEL%
