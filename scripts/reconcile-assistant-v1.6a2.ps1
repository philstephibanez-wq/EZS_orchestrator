# EZStudioLab Assistant v1.6a(2) reconciliation: MAIN source + XPS web.
# Windows PowerShell 5.1. No scientific workers or Guardian tasks are stopped.
[CmdletBinding()]
param(
    [string]$Source = 'H:\EZStudioLab_assistant',
    [string]$Node = 'steph@192.168.1.81',
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
function Run-Git([string]$Root, [string[]]$GitArgs) {
    if (-not (Test-Path -LiteralPath (Join-Path $Root '.git'))) { throw "NOT_GIT_REPOSITORY: $Root" }
    & git -C $Root @GitArgs
    if ($LASTEXITCODE -ne 0) { throw "GIT_FAILED: $Root $($GitArgs -join ' ')" }
}
function Remote([string]$Script) {
    $bytes = [System.Text.Encoding]::Unicode.GetBytes($Script)
    $encoded = [Convert]::ToBase64String($bytes)
    & ssh $Node powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand $encoded
    if ($LASTEXITCODE -ne 0) { throw "REMOTE_FAILED: rc=$LASTEXITCODE" }
}
if (-not (Test-Path -LiteralPath $Source)) { throw "MAIN_SOURCE_NOT_FOUND: $Source" }
Write-Output '=== MAIN ASSISTANT SOURCE ==='
Run-Git $Source @('status','--short')
Run-Git $Source @('rev-parse','--short','HEAD')
$mainVersion = (Get-Content (Join-Path $Source 'VERSION') -Raw).Trim()
Write-Output "MAIN_VERSION=$mainVersion"
if ($Apply) {
    $dirty = @(& git -C $Source status --porcelain)
    if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) { throw 'MAIN_SOURCE_DIRTY_ABORT' }
    Run-Git $Source @('pull','--ff-only','origin','main')
    $mainVersion = (Get-Content (Join-Path $Source 'VERSION') -Raw).Trim()
    if ($mainVersion -ne '1.6a(2)') { throw "MAIN_VERSION_UNEXPECTED=$mainVersion" }
}
$remoteScript = @'
$ErrorActionPreference = 'Stop'
$root = 'C:\EZStudioLab_assistant'
if (-not (Test-Path -LiteralPath (Join-Path $root '.git'))) { throw 'XPS_GIT_REPOSITORY_MISSING' }
Write-Output '=== XPS ASSISTANT ==='
git -C $root rev-parse --short HEAD
if ($LASTEXITCODE -ne 0) { throw 'XPS_HEAD_FAILED' }
$version = (Get-Content (Join-Path $root 'VERSION') -Raw).Trim()
Write-Output "XPS_VERSION=$version"
$worker = @(Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'profile_ai_requests_worker.py' })
Write-Output "PROFILE_WORKER_COUNT=$($worker.Count)"
foreach ($item in $worker) { Write-Output "PROFILE_WORKER_PID=$($item.ProcessId)" }
'@
Remote $remoteScript
if (-not $Apply) {
    Write-Output 'READ_ONLY_OK. Re-run with -Apply to update and restart only the XPS web dashboard.'
    exit 0
}
$applyRemote = @'
$ErrorActionPreference = 'Stop'
$root = 'C:\EZStudioLab_assistant'
$dirty = @(git -C $root status --porcelain)
if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) { throw 'XPS_SOURCE_DIRTY_ABORT' }
git -C $root pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw 'XPS_PULL_FAILED' }
$version = (Get-Content (Join-Path $root 'VERSION') -Raw).Trim()
if ($version -ne '1.6a(2)') { throw "XPS_VERSION_UNEXPECTED=$version" }
Push-Location $root
try {
    python -m unittest discover -s tests -p test_profile_dashboard_v16a2.py -v
    if ($LASTEXITCODE -ne 0) { throw 'XPS_TEST_FAILED' }
    python -m py_compile app\web_status.py
    if ($LASTEXITCODE -ne 0) { throw 'XPS_COMPILE_FAILED' }
    # Web lifecycle scripts guard ownership of both ports 8712/8713.
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'scripts\stop-web.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'XPS_WEB_STOP_FAILED' }
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $root 'scripts\start-web.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'XPS_WEB_START_FAILED' }
    $status = Invoke-RestMethod -Uri 'http://127.0.0.1:8713/api/status' -TimeoutSec 8
    $pc = $status.profile_consultation
    if ($null -eq $pc) { throw 'XPS_WEB_MISSING_PROFILE_STATUS' }
    Write-Output ("PROFILE_PROGRESS=" + ($pc | ConvertTo-Json -Compress -Depth 7))
    Write-Output 'V16A2_XPS_WEB_DEPLOY_OK'
} finally { Pop-Location }
'@
Remote $applyRemote
Write-Output 'MAIN_SOURCE_XPS_WEB_RECONCILED'
