@echo off
setlocal
cd /d "%~dp0"

set "PYTHON=H:\Python\pythoncore-3.14-64\python.exe"

echo [EZS] Arret du worker permanent uniquement...
"%PYTHON%" -m service.service_cli stop --wait-seconds 20
set "RC=%ERRORLEVEL%"

if "%RC%"=="0" (
  echo [EZS] Worker arrete.
  exit /b 0
)

echo [EZS] Arret normal non confirme. Verification d'un metadata stale...
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command ^
  "$meta = Join-Path (Get-Location) 'runtime\service\service.json';" ^
  "$stop = Join-Path (Get-Location) 'runtime\service\stop.request';" ^
  "if (-not (Test-Path $meta)) { exit 0 };" ^
  "try { $m = Get-Content -Raw -Encoding UTF8 $meta | ConvertFrom-Json; $pidValue = [int]$m.pid } catch { exit 2 };" ^
  "$p = Get-Process -Id $pidValue -ErrorAction SilentlyContinue;" ^
  "if ($null -eq $p) { Remove-Item $meta -Force -ErrorAction SilentlyContinue; Remove-Item $stop -Force -ErrorAction SilentlyContinue; Write-Host '[EZS] Metadata stale nettoye; aucun worker actif.'; exit 0 };" ^
  "Write-Host ('[EZS] Worker encore actif pid=' + $pidValue + '. Aucun kill force.'); exit 3"
set "RC=%ERRORLEVEL%"

exit /b %RC%
