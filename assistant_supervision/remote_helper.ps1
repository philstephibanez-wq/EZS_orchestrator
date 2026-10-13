param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start","stop")]
    [string]$Command
)

$ErrorActionPreference = "Stop"

$hostRepo = $PSScriptRoot
$root = Split-Path -Parent $hostRepo
$app = Join-Path $root "app\main.py"
$statusWindow = Join-Path $root "app\status_window.pyw"
$logs = Join-Path $root "logs"
$profileRuntime = Join-Path $env:LOCALAPPDATA "EZStudioLab_assistant\runtime"
$profileStatePath = Join-Path $profileRuntime "profile-review-watch.state.json"
$stdoutPath = Join-Path $logs "assistant.out.log"
$stderrPath = Join-Path $logs "assistant.err.log"
$profileStdoutPath = Join-Path $logs "profile-review.out.log"
$profileStderrPath = Join-Path $logs "profile-review.err.log"

function Get-DistributedMatches {
    @(
        Get-CimInstance Win32_Process | Where-Object {
            $_.CommandLine -and
            $_.CommandLine -like "*EZStudioLab_assistant*app*main.py*" -and
            $_.CommandLine -like "*distributed-watch*"
        }
    )
}

function Get-ProfileMatches {
    @(
        Get-CimInstance Win32_Process | Where-Object {
            $_.CommandLine -and
            $_.CommandLine -like "*EZStudioLab_assistant*app*main.py*" -and
            $_.CommandLine -like "*profile-review-auto-watch*"
        }
    )
}

if ($Command -eq "stop") {
    $matches = @((Get-DistributedMatches) + (Get-ProfileMatches))
    foreach ($proc in $matches) {
        Stop-Process -Id ([int]$proc.ProcessId) -Force -ErrorAction Stop
    }

    $statusPath = Join-Path $logs "assistant.status.json"
    $payload = [ordered]@{
        schema = "ezstudio.assistant-local-status.v1"
        state = "STOPPED"
        activity = "Assistant arrêté par Orchestrator"
        at_epoch = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0
        at = [DateTime]::UtcNow.ToString("o")
    }
    New-Item -ItemType Directory -Path (Split-Path $statusPath) -Force | Out-Null
    $tmp = $statusPath + ".tmp"
    $payload | ConvertTo-Json -Compress | Set-Content -LiteralPath $tmp -Encoding utf8
    Move-Item -LiteralPath $tmp -Destination $statusPath -Force

    Write-Output "EZS_ASSISTANT_SUPERVISION_STOP_OK"
    exit 0
}

if (-not (Test-Path -LiteralPath $app -PathType Leaf)) {
    throw "assistant_app_missing"
}
if (-not (Test-Path -LiteralPath $statusWindow -PathType Leaf)) {
    throw "assistant_status_window_missing"
}
if (-not (Test-Path -LiteralPath (Join-Path $hostRepo "python\ezstudio\distributed\capabilities.py") -PathType Leaf)) {
    throw "assistant_runtime_missing"
}

$distributedMatches = @(Get-DistributedMatches)
$profileMatches = @(Get-ProfileMatches)

if ($distributedMatches.Count -gt 1) {
    throw "assistant_duplicate_distributed_processes:$($distributedMatches.Count)"
}
if ($profileMatches.Count -gt 1) {
    throw "assistant_duplicate_profile_processes:$($profileMatches.Count)"
}

$token = [Console]::In.ReadLine()
if ([string]::IsNullOrWhiteSpace($token)) {
    throw "assistant_token_stdin_missing"
}

$python = (Get-Command python -ErrorAction Stop).Source
New-Item -ItemType Directory -Path $logs -Force | Out-Null
New-Item -ItemType Directory -Path $profileRuntime -Force | Out-Null

$env:EZSTUDIOLAB_ASSISTANT_TOKEN = $token
$env:EZSTUDIOLAB_ASSISTANT_BASE_URL = "http://EZSTUDIO-MAIN:8702"
$env:EZSTUDIOLAB_ASSISTANT_NODE_ID = "EZStudioLab_assistant-EZSTUDIO-XPS"
$env:EZSTUDIOLAB_HOST_REPO = $hostRepo
$env:EZSTUDIO_SHARED_MODEL_ROOT = "\\EZSTUDIO-MAIN\EZModels"
$env:EZSTUDIOLAB_ASSISTANT_MODEL_CACHE = Join-Path $root "models"
$env:EZSTUDIOLAB_ASSISTANT_STATUS_FILE = Join-Path $logs "assistant.status.json"
$env:PYTHONPATH = Join-Path $hostRepo "python"

if ($distributedMatches.Count -eq 0) {
    $distributed = Start-Process -FilePath $python -ArgumentList @(
        $app,
        "distributed-watch",
        "--poll-seconds","5",
        "--limit","100"
    ) -WorkingDirectory $root -WindowStyle Hidden -PassThru `
      -RedirectStandardOutput $stdoutPath `
      -RedirectStandardError $stderrPath
    Start-Sleep -Milliseconds 900
    if ($distributed.HasExited) {
        throw "assistant_distributed_start_exited:$($distributed.ExitCode)"
    }
}

if ($profileMatches.Count -eq 0) {
    $profile = Start-Process -FilePath $python -ArgumentList @(
        $app,
        "profile-review-auto-watch",
        "--state-file",$profileStatePath,
        "--poll-seconds","900",
        "--draft-cooldown-hours","24",
        "--abstain-cooldown-hours","168",
        "--limit","100",
        "--max-items","5",
        "--min-confidence","0.75",
        "--network-min-interval","2",
        "--network-max-response-kb","256",
        "--network-max-requests","6"
    ) -WorkingDirectory $root -WindowStyle Hidden -PassThru `
      -RedirectStandardOutput $profileStdoutPath `
      -RedirectStandardError $profileStderrPath
    Start-Sleep -Milliseconds 900
    if ($profile.HasExited) {
        throw "assistant_profile_start_exited:$($profile.ExitCode)"
    }
}

$taskName = "EZStudioLab Assistant Status"
$existingStatusTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($null -ne $existingStatusTask) {
    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
}
$pythonw = (Get-Command pythonw.exe -ErrorAction Stop).Source
$action = New-ScheduledTaskAction `
    -Execute $pythonw `
    -Argument ('"' + $statusWindow + '" --root "' + $root + '"')
$principal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited
Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Principal $principal `
    -Description "Fenêtre locale de statut EZStudioLab Assistant" `
    -Force | Out-Null
Start-ScheduledTask -TaskName $taskName

Write-Output "EZS_ASSISTANT_SUPERVISION_START_OK"
