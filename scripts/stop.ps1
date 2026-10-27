$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'v2_lifecycle.ps1') -Action stop
