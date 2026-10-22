# Targeted deploy of Assistant v1.6a(3) to XPS, preserving Guardian/web/LAB.
# Run from MAIN after verifying no PROFILE job currently running.
[CmdletBinding()]
param([string]$Node='steph@192.168.1.81')
$ErrorActionPreference='Stop'
$mainSource='H:\EZStudioLab_assistant'
if (-not (Test-Path -LiteralPath (Join-Path $mainSource '.git'))) { throw 'MAIN_ASSISTANT_SOURCE_MISSING' }
$dirtyMain=@(git -C $mainSource status --porcelain)
if ($LASTEXITCODE -ne 0 -or $dirtyMain.Count -ne 0) { throw 'MAIN_ASSISTANT_SOURCE_DIRTY' }
git -C $mainSource pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw 'MAIN_ASSISTANT_PULL_FAILED' }
$mainVersion=(Get-Content (Join-Path $mainSource 'VERSION') -Raw).Trim()
if ($mainVersion -ne '1.6a(3)') { throw "MAIN_VERSION_UNEXPECTED=$mainVersion" }
$remote=@'
$ErrorActionPreference='Stop'
$root='C:\EZStudioLab_assistant'
if (-not (Test-Path -LiteralPath (Join-Path $root '.git'))) { throw 'ASSISTANT_REPO_MISSING' }
$dirty=@(git -C $root status --porcelain)
if ($LASTEXITCODE -ne 0) { throw 'GIT_STATUS_FAILED' }
$tracked=@($dirty | Where-Object { $_ -notmatch '^\?\? ' })
if ($tracked.Count -gt 0) {
    $tracked | ForEach-Object { Write-Output "TRACKED_MODIFICATION=$_"}
    throw 'TRACKED_CHANGES_ABORT'
}
Write-Output 'XPS_UNTRACKED_PRESERVED:'
$dirty | Where-Object { $_ -match '^\?\? ' } | ForEach-Object { Write-Output $_ }
git -C $root pull --ff-only origin main
if ($LASTEXITCODE -ne 0) { throw 'GIT_PULL_FAILED' }
$version=(Get-Content (Join-Path $root 'VERSION') -Raw).Trim()
if ($version -ne '1.6a(3)') { throw "VERSION_UNEXPECTED=$version" }
Push-Location $root
try {
    python -m unittest discover -s tests -p 'test_profile*16a*.py' -v
    if ($LASTEXITCODE -ne 0) { throw 'PYTHON_TEST_FAILED' }
    python -m py_compile app\profile_final_verifier.py app\profile_auto_review.py runtime\profile_ai_requests_worker.py
    if ($LASTEXITCODE -ne 0) { throw 'PYTHON_COMPILE_FAILED' }
    $workers=@(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^python(?:w)?\.exe$' -and
        $_.CommandLine -match 'profile_ai_requests_worker\.py'
    })
    if ($workers.Count -ne 1) { throw "PROFILE_WORKER_COUNT_UNEXPECTED=$($workers.Count)" }
    $pidOld=[int]$workers[0].ProcessId
    # This script only stops the known PROFILE worker; Guardian must restart it.
    Stop-Process -Id $pidOld -ErrorAction Stop
    $deadline=[DateTime]::UtcNow.AddSeconds(25)
    do {
        Start-Sleep -Seconds 1
        $after=@(Get-CimInstance Win32_Process | Where-Object {
            $_.Name -match '^python(?:w)?\.exe$' -and
            $_.CommandLine -match 'profile_ai_requests_worker\.py'
        })
        if ($after.Count -eq 1 -and $after[0].ProcessId -ne $pidOld) { break }
        if ($after.Count -gt 1) { throw 'PROFILE_WORKER_DUPLICATE_AFTER_RESTART' }
    } while ([DateTime]::UtcNow -lt $deadline)
    if ($after.Count -ne 1 -or $after[0].ProcessId -eq $pidOld) { throw 'GUARDIAN_PROFILE_RESTART_NOT_CONFIRMED' }
    $api=Invoke-RestMethod -Uri 'http://127.0.0.1:8713/api/status' -TimeoutSec 8
    if (-not $api.profile_consultation) { throw 'WEB_PROFILE_STATUS_MISSING' }
    Write-Output "XPS_PROFILE_RESTART=$pidOld->$($after[0].ProcessId)"
    Write-Output "XPS_VERSION=$version"
    Write-Output 'V16A3_PROFILE_DEPLOY_OK'
} finally { Pop-Location }
'@
$encoded=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($remote))
& ssh $Node powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand $encoded
if ($LASTEXITCODE -ne 0) { throw "V16A3_REMOTE_DEPLOY_FAILED:$LASTEXITCODE" }
