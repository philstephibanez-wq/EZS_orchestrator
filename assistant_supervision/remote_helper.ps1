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
$secretPath = Join-Path $profileRuntime "analysis-worker-token.dpapi"
$stdoutPath = Join-Path $logs "assistant.out.log"
$stderrPath = Join-Path $logs "assistant.err.log"
$profileStdoutPath = Join-Path $logs "profile-review.out.log"
$profileStderrPath = Join-Path $logs "profile-review.err.log"

$distributedTaskName = "EZStudioLab Assistant Distributed"
$profileTaskName = "EZStudioLab Assistant Profile"
$statusTaskName = "EZStudioLab Assistant Status"

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

function Remove-TaskExact {
    param([Parameter(Mandatory=$true)][string]$TaskName)

    $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -ne $task) {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction Stop
    }
}

function Register-PersistentTask {
    param(
        [Parameter(Mandatory=$true)][string]$TaskName,
        [Parameter(Mandatory=$true)][string]$EncodedCommand,
        [Parameter(Mandatory=$true)][string]$Description
    )

    Remove-TaskExact -TaskName $TaskName

    $action = New-ScheduledTaskAction `
        -Execute "powershell.exe" `
        -Argument ("-NoProfile -NonInteractive -ExecutionPolicy Bypass -EncodedCommand " + $EncodedCommand)

    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Limited

    $settings = New-ScheduledTaskSettingsSet `
        -MultipleInstances IgnoreNew `
        -ExecutionTimeLimit ([TimeSpan]::Zero) `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries

    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Principal $principal `
        -Settings $settings `
        -Description $Description `
        -Force | Out-Null

    Start-ScheduledTask -TaskName $TaskName
}

function Protect-AssistantToken {
    param([Parameter(Mandatory=$true)][string]$Token)

    $secure = ConvertTo-SecureString $Token -AsPlainText -Force
    $cipher = ConvertFrom-SecureString $secure
    [System.IO.File]::WriteAllText(
        $secretPath,
        $cipher,
        [System.Text.Encoding]::ASCII
    )
}

function New-WorkerEncodedCommand {
    param(
        [Parameter(Mandatory=$true)]
        [ValidateSet("distributed","profile")]
        [string]$Mode,
        [Parameter(Mandatory=$true)][string]$Python
    )

    $common = @"
`$ErrorActionPreference = 'Stop'
`$cipher = ([System.IO.File]::ReadAllText('$secretPath',[System.Text.Encoding]::ASCII)).Trim()
`$secure = ConvertTo-SecureString `$cipher
`$credential = New-Object System.Management.Automation.PSCredential('assistant-token',`$secure)
`$env:EZSTUDIOLAB_ASSISTANT_TOKEN = `$credential.GetNetworkCredential().Password
`$env:EZSTUDIOLAB_ASSISTANT_BASE_URL = 'http://EZSTUDIO-MAIN:8702'
`$env:EZSTUDIOLAB_ASSISTANT_NODE_ID = 'EZStudioLab_assistant-EZSTUDIO-XPS'
`$env:EZSTUDIOLAB_HOST_REPO = '$hostRepo'
`$env:EZSTUDIO_SHARED_MODEL_ROOT = '\\EZSTUDIO-MAIN\EZModels'
`$env:EZSTUDIOLAB_ASSISTANT_MODEL_CACHE = '$root\models'
`$env:EZSTUDIOLAB_ASSISTANT_STATUS_FILE = '$logs\assistant.status.json'
`$env:PYTHONPATH = '$hostRepo\python'
"@

    if ($Mode -eq "distributed") {
        $body = @"
`$process = Start-Process -FilePath '$Python' -ArgumentList @(
    '$app',
    "distributed-watch",
    "--poll-seconds","5",
    "--limit","100"
) -WorkingDirectory '$root' -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput '$stdoutPath' -RedirectStandardError '$stderrPath'
exit `$process.ExitCode
"@
    }
    else {
        $body = @"
`$process = Start-Process -FilePath '$Python' -ArgumentList @(
    '$app',
    "profile-review-auto-watch",
    "--state-file","$profileStatePath",
    "--poll-seconds","900",
    "--draft-cooldown-hours","24",
    "--abstain-cooldown-hours","168",
    "--limit","100",
    "--max-items","5",
    "--min-confidence","0.75",
    "--network-min-interval","2",
    "--network-max-response-kb","256",
    "--network-max-requests","6"
) -WorkingDirectory '$root' -WindowStyle Hidden -PassThru -Wait -RedirectStandardOutput '$profileStdoutPath' -RedirectStandardError '$profileStderrPath'
exit `$process.ExitCode
"@
    }

    $script = $common + [Environment]::NewLine + $body
    return [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($script))
}

function Wait-ForSingleton {
    param(
        [Parameter(Mandatory=$true)][ValidateSet("distributed","profile")][string]$Mode,
        [int]$Seconds = 10
    )

    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        $matches = if ($Mode -eq "distributed") {
            @(Get-DistributedMatches)
        }
        else {
            @(Get-ProfileMatches)
        }

        if ($matches.Count -eq 1) {
            return
        }
        if ($matches.Count -gt 1) {
            throw "assistant_${Mode}_duplicate_after_task_start:$($matches.Count)"
        }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)

    throw "assistant_${Mode}_task_start_timeout"
}

if ($Command -eq "stop") {
    foreach ($taskName in @($distributedTaskName,$profileTaskName,$statusTaskName)) {
        Remove-TaskExact -TaskName $taskName
    }

    $matches = @((Get-DistributedMatches) + (Get-ProfileMatches))
    foreach ($proc in $matches) {
        Stop-Process -Id ([int]$proc.ProcessId) -Force -ErrorAction Stop
    }

    Remove-Item -LiteralPath $secretPath -Force -ErrorAction SilentlyContinue

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
$pythonw = (Get-Command pythonw.exe -ErrorAction Stop).Source

New-Item -ItemType Directory -Path $logs -Force | Out-Null
New-Item -ItemType Directory -Path $profileRuntime -Force | Out-Null
Protect-AssistantToken -Token $token
$token = $null

if ($distributedMatches.Count -eq 0) {
    $distributedEncoded = New-WorkerEncodedCommand -Mode distributed -Python $python
    Register-PersistentTask `
        -TaskName $distributedTaskName `
        -EncodedCommand $distributedEncoded `
        -Description "Worker distribué persistant EZStudioLab Assistant"
    Wait-ForSingleton -Mode distributed
}

if ($profileMatches.Count -eq 0) {
    $profileEncoded = New-WorkerEncodedCommand -Mode profile -Python $python
    Register-PersistentTask `
        -TaskName $profileTaskName `
        -EncodedCommand $profileEncoded `
        -Description "Profile review watch persistant EZStudioLab Assistant"
    Wait-ForSingleton -Mode profile
}

Remove-TaskExact -TaskName $statusTaskName
$statusAction = New-ScheduledTaskAction `
    -Execute $pythonw `
    -Argument ('"' + $statusWindow + '" --root "' + $root + '"')
$statusPrincipal = New-ScheduledTaskPrincipal `
    -UserId $env:USERNAME `
    -LogonType Interactive `
    -RunLevel Limited
$statusSettings = New-ScheduledTaskSettingsSet `
    -MultipleInstances IgnoreNew `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries
Register-ScheduledTask `
    -TaskName $statusTaskName `
    -Action $statusAction `
    -Principal $statusPrincipal `
    -Settings $statusSettings `
    -Description "Fenêtre locale de statut EZStudioLab Assistant" `
    -Force | Out-Null
Start-ScheduledTask -TaskName $statusTaskName

Write-Output "EZS_ASSISTANT_SUPERVISION_START_OK"
