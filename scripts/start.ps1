# EZS Orchestrator v2.a0 — bootstrap boundary, fail closed until native lifecycle is commissioned.
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path -LiteralPath (Join-Path $root 'bin\console'))) { throw 'SYMFONY_ROOT_MISSING' }
throw 'EZS_V2_START_NOT_READY: lifecycle natif Symfony non valide. Aucun service demarre.'
