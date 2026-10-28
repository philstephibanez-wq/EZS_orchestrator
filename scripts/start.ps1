$ErrorActionPreference = 'Stop'
# DEV only. PROD gateway 8510/18515 is strictly outside this launcher.
& (Join-Path $PSScriptRoot 'v2_lifecycle.ps1') -Action start
if (-not $?) { throw 'EZS_DEV_START_FAILED' }
