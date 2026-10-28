$ErrorActionPreference = 'Stop'
# DEV only. Never terminate PROD gateway or EZScore infrastructure.
& (Join-Path $PSScriptRoot 'v2_lifecycle.ps1') -Action stop
if (-not $?) { throw 'EZS_DEV_STOP_FAILED' }
