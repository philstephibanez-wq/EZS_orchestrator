#Requires -Version 5.1
# Deploy only the orchestrator permanent service; do not restart DEV/PROD/LAB servers.
[CmdletBinding()]
param()
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$reportDir = Join-Path $root 'runtime\deploy'
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$reportFile = Join-Path $reportDir 'latest.json'
$started = [DateTimeOffset]::UtcNow.ToString('o')
$checks = [ordered]@{}
$state = 'DEPLOY_FAILED'
$failure = $null
$version = $null
$sha = $null
$python = 'H:\Python\pythoncore-3.14-64\python.exe'
try {
    $branch = (& git -C $root branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or $branch -ne 'master') { throw "DEPLOY_BRANCH_INVALID:$branch" }
    $checks.branch = $branch
    $dirty = @(& git -C $root status --porcelain --untracked-files=no)
    if ($LASTEXITCODE -ne 0 -or $dirty.Count -gt 0) { throw 'DEPLOY_TRACKED_TREE_DIRTY' }
    & git -C $root fetch --quiet origin master
    if ($LASTEXITCODE -ne 0) { throw 'DEPLOY_FETCH_FAILED' }
    $localSha = (& git -C $root rev-parse HEAD).Trim()
    $upstreamSha = (& git -C $root rev-parse origin/master).Trim()
    $baseSha = (& git -C $root merge-base HEAD origin/master).Trim()
    if ($LASTEXITCODE -ne 0 -or $baseSha -ne $localSha) { throw 'DEPLOY_NOT_FAST_FORWARD' }
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { throw 'DEPLOY_PYTHON_MISSING' }
    $checks.python = $python
    & git -C $root merge --ff-only origin/master
    if ($LASTEXITCODE -ne 0) { throw 'DEPLOY_MERGE_FAILED' }
    $sha = (& git -C $root rev-parse HEAD).Trim()
    $version = (Get-Content -LiteralPath (Join-Path $root 'VERSION') -Raw).Trim()
    if ($version -notmatch '^\d+\.\d+[a-z]$') { throw 'DEPLOY_VERSION_INVALID' }
    $checks.source = "version=$version;sha=$sha"
    $checkScript = 'from config.loader import load_runtime_config; c=load_runtime_config(); assert c.assistant_xps_url.startswith(("http://","https://")); print(c.assistant_xps_url)'
    $xpsUrl = (& $python -c $checkScript).Trim()
    if ($LASTEXITCODE -ne 0) { throw 'DEPLOY_XPS_CONFIG_INVALID' }
    $checks.xps_url = $xpsUrl
    $health = Invoke-RestMethod -Uri ($xpsUrl.TrimEnd('/') + '/api/health') -TimeoutSec 8 -ErrorAction Stop
    if ($health.ok -ne $true -or $health.persistence_owner -ne 'LAB' -or -not $health.version) {
        throw 'DEPLOY_XPS_HEALTH_INVALID'
    }
    $checks.xps_health = "version=$($health.version);owner=LAB"

    # Fail closed if a scientific execution is underway; never report success if skipped.
    $active = & $python -c 'from config.loader import load_runtime_config; from runtime_guard.activity import analysis_execution_active; c=load_runtime_config(); print("active" if analysis_execution_active(c.orchestrator_root / "runtime") else "idle")'
    if ($LASTEXITCODE -ne 0 -or $active -ne 'idle') { throw 'DEPLOY_EXECUTION_ACTIVE_OR_UNKNOWN' }
    $checks.science = 'idle'

    $restartOutput = & $python -m service.service_cli restart-if-idle --target all --poll-seconds 2.0
    if ($LASTEXITCODE -ne 0 -or $restartOutput -match 'SERVICE_RELOAD_SKIPPED') { throw 'DEPLOY_SERVICE_RESTART_FAILED_OR_SKIPPED' }
    # A restart-if-idle may legitimately skip an active execution. Never call that deployed.
    $serviceOutput = & $python -m service.service_cli status
    if ($LASTEXITCODE -ne 0 -or $serviceOutput -notmatch 'SERVICE: running pid=(\d+) target=all') {
        throw "DEPLOY_SERVICE_STATUS_UNVERIFIED:$serviceOutput"
    }
    $pidValue = [int]$Matches[1]
    $metaPath = Join-Path $root 'runtime\service\service.json'
    $meta = Get-Content -LiteralPath $metaPath -Raw | ConvertFrom-Json
    if ([int]$meta.pid -ne $pidValue) { throw 'DEPLOY_PID_METADATA_MISMATCH' }
    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$pidValue" -ErrorAction Stop
    if ($null -eq $proc -or $proc.CommandLine -notmatch 'service\.service_cli run') {
        throw 'DEPLOY_PROCESS_IDENTITY_MISMATCH'
    }
    $checks.service = "pid=$pidValue;target=all"
    $state = 'DEPLOYED_OK'
} catch {
    $failure = $_.Exception.Message
} finally {
    $report = [ordered]@{
        schema = 'ezs.orchestrator.deployment.v1'
        state = $state
        started_at = $started
        finished_at = [DateTimeOffset]::UtcNow.ToString('o')
        root = $root
        version = $version
        sha = $sha
        checks = $checks
        failure = $failure
        profile_e2e_validated = $false
    }
    $report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $reportFile -Encoding UTF8
    Write-Output $state
    Write-Output "REPORT=$reportFile"
    if ($failure) { Write-Output "ERROR=$failure" }
}
if ($state -ne 'DEPLOYED_OK') { exit 1 }
