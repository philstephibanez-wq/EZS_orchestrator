param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start","stop")]
    [string]$Command
)

$ErrorActionPreference = "Stop"

$hostRepo = $PSScriptRoot
$root = "C:\EZStudioLab_assistant"
$app = Join-Path $root "app\main.py"
$logs = Join-Path $root "logs"
$profileRuntime = Join-Path $root "runtime\state"
$profileStatePath = Join-Path $profileRuntime "profile-review-watch.state.json"
$secretPath = Join-Path $profileRuntime "analysis-worker-token.dpapi"
$hiddenLauncherPath = Join-Path $profileRuntime "assistant-worker-hidden.vbs"
$stdoutPath = Join-Path $logs "assistant.out.log"
$stderrPath = Join-Path $logs "assistant.err.log"
$profileStdoutPath = Join-Path $logs "profile-review.out.log"
$profileStderrPath = Join-Path $logs "profile-review.err.log"
$webStartPath = Join-Path $root "scripts\start.cmd"
$webStopPath = Join-Path $root "scripts\stop.cmd"

$distributedTaskName = "EZStudioLab Assistant Distributed"
$profileTaskName = "EZStudioLab Assistant Profile"
$webTaskName = "EZStudioLab Assistant Web"

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

function Ensure-HiddenTaskLauncher {
    $launcher = @'
Set shell = CreateObject("WScript.Shell")
If WScript.Arguments.Count <> 1 Then WScript.Quit 64
cmd = "powershell.exe -NoProfile -NonInteractive -WindowStyle Hidden -ExecutionPolicy Bypass -EncodedCommand " & WScript.Arguments(0)
rc = shell.Run(cmd, 0, True)
WScript.Quit rc
'@
    [System.IO.File]::WriteAllText(
        $hiddenLauncherPath,
        $launcher,
        [System.Text.Encoding]::ASCII
    )
}

function Register-PersistentTask {
    param(
        [Parameter(Mandatory=$true)][string]$TaskName,
        [Parameter(Mandatory=$true)][string]$EncodedCommand,
        [Parameter(Mandatory=$true)][string]$Description
    )

    Remove-TaskExact -TaskName $TaskName

    $action = New-ScheduledTaskAction `
        -Execute "wscript.exe" `
        -Argument ('"' + $hiddenLauncherPath + '" "' + $EncodedCommand + '"')

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

function New-WebEncodedCommand {
    $script = @"
`$ErrorActionPreference = 'Stop'
`$cipher = ([System.IO.File]::ReadAllText('$secretPath',[System.Text.Encoding]::ASCII)).Trim()
`$secure = ConvertTo-SecureString `$cipher
`$credential = New-Object System.Management.Automation.PSCredential('assistant-token',`$secure)
`$env:EZSTUDIOLAB_ASSISTANT_TOKEN = `$credential.GetNetworkCredential().Password
`$env:EZSTUDIOLAB_ASSISTANT_BASE_URL = 'http://EZSTUDIO-MAIN:8702'
`$env:EZSTUDIOLAB_ASSISTANT_NODE_ID = 'EZStudioLab_assistant-EZSTUDIO-XPS'
`$env:EZSTUDIO_SHARED_MODEL_ROOT = '\\EZSTUDIO-MAIN\EZModels'
`$env:EZSTUDIOLAB_ASSISTANT_STATUS_FILE = '$logs\assistant.status.json'

# Scheduled tasks do not reliably inherit a refreshed user PATH/environment.
# Re-read the persistent PHP override explicitly at every Web task launch.
`$phpOverride = [Environment]::GetEnvironmentVariable('EZS_ASSISTANT_PHP','User')
if ([string]::IsNullOrWhiteSpace(`$phpOverride)) {
    `$phpOverride = [Environment]::GetEnvironmentVariable('EZS_ASSISTANT_PHP','Machine')
}
if (-not [string]::IsNullOrWhiteSpace(`$phpOverride)) {
    `$env:EZS_ASSISTANT_PHP = `$phpOverride
}

& '$webStartPath'
if (`$LASTEXITCODE -ne 0) {
    throw "assistant_web_start_failed:`$LASTEXITCODE"
}

Start-Sleep -Milliseconds 800

while (`$true) {
    `$listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8712,8713 -ErrorAction SilentlyContinue)
    `$ports = @(`$listeners | Select-Object -ExpandProperty LocalPort -Unique)
    if (-not (`$ports -contains 8712) -or -not (`$ports -contains 8713)) {
        throw 'assistant_web_listener_lost'
    }
    Start-Sleep -Seconds 10
}
"@
    return [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($script))
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

if ($Command -eq "stop") {
    foreach ($taskName in @($distributedTaskName,$profileTaskName,$webTaskName,"EZStudioLab Assistant Status")) {
        Remove-TaskExact -TaskName $taskName
    }

    $matches = @()
    $matches += @(Get-DistributedMatches)
    $matches += @(Get-ProfileMatches)
    foreach ($proc in $matches) {
        if ($null -eq $proc) {
            continue
        }
        $pidValue = [int]$proc.ProcessId
        if ($pidValue -le 0) {
            continue
        }
        Stop-Process -Id $pidValue -Force -ErrorAction Stop
    }

    if (Test-Path -LiteralPath $webStopPath -PathType Leaf) {
        & $webStopPath
        if ($LASTEXITCODE -ne 0) {
            throw "assistant_web_stop_failed:$LASTEXITCODE"
        }
    }

    Start-Sleep -Milliseconds 400
    $webListeners = @(Get-NetTCPConnection -State Listen -LocalPort 8712,8713 -ErrorAction SilentlyContinue)
    if ($webListeners.Count -ne 0) {
        $owners = ($webListeners | ForEach-Object { "$($_.LocalPort):$($_.OwningProcess)" }) -join ","
        throw "assistant_web_stop_incomplete:$owners"
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
if (-not (Test-Path -LiteralPath (Join-Path $hostRepo "python\ezstudio\distributed\capabilities.py") -PathType Leaf)) {
    throw "assistant_runtime_missing"
}
if (-not (Test-Path -LiteralPath $webStartPath -PathType Leaf)) {
    throw "assistant_web_start_missing"
}
if (-not (Test-Path -LiteralPath $webStopPath -PathType Leaf)) {
    throw "assistant_web_stop_missing"
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

New-Item -ItemType Directory -Path $logs -Force | Out-Null
New-Item -ItemType Directory -Path $profileRuntime -Force | Out-Null
Ensure-HiddenTaskLauncher
Protect-AssistantToken -Token $token

# Repair a recognized partial Web instance without stopping distributed/profile
# workers. Typical case: PHP 8713 was killed while Caddy 8712 is still alive.
$preWebListeners = @(Get-NetTCPConnection -State Listen -LocalPort 8712,8713 -ErrorAction SilentlyContinue)
$preWebPorts = @($preWebListeners | Select-Object -ExpandProperty LocalPort -Unique)
$webHas8712 = ($preWebPorts -contains 8712)
$webHas8713 = ($preWebPorts -contains 8713)

if ($webHas8712 -xor $webHas8713) {
    & $webStopPath
    if ($LASTEXITCODE -ne 0) {
        throw "assistant_web_partial_repair_stop_failed:$LASTEXITCODE"
    }

    Start-Sleep -Milliseconds 400
    $remainingWebListeners = @(Get-NetTCPConnection -State Listen -LocalPort 8712,8713 -ErrorAction SilentlyContinue)
    if ($remainingWebListeners.Count -ne 0) {
        $owners = ($remainingWebListeners | ForEach-Object { "$($_.LocalPort):$($_.OwningProcess)" }) -join ","
        throw "assistant_web_partial_repair_incomplete:$owners"
    }

    Write-Output "EZS_ASSISTANT_WEB_PARTIAL_REPAIR_READY"
}

$webEncoded = New-WebEncodedCommand
Register-PersistentTask `
    -TaskName $webTaskName `
    -EncodedCommand $webEncoded `
    -Description "Web persistant EZStudioLab Assistant"

$deadline = [DateTime]::UtcNow.AddSeconds(20)
do {
    Start-Sleep -Milliseconds 250
    $webListeners = @(Get-NetTCPConnection -State Listen -LocalPort 8712,8713 -ErrorAction SilentlyContinue)
    $webPorts = @($webListeners | Select-Object -ExpandProperty LocalPort -Unique)
    if (($webPorts -contains 8712) -and ($webPorts -contains 8713)) {
        break
    }
} while ([DateTime]::UtcNow -lt $deadline)

if (-not ($webPorts -contains 8712) -or -not ($webPorts -contains 8713)) {
    throw "assistant_web_start_listener_missing"
}

$python = (Get-Command python -ErrorAction Stop).Source

$token = $null

if ($distributedMatches.Count -eq 0) {
    $distributedEncoded = New-WorkerEncodedCommand -Mode distributed -Python $python
    Register-PersistentTask `
        -TaskName $distributedTaskName `
        -EncodedCommand $distributedEncoded `
        -Description "Worker distribué persistant EZStudioLab Assistant"
}

if ($profileMatches.Count -eq 0) {
    $profileEncoded = New-WorkerEncodedCommand -Mode profile -Python $python
    Register-PersistentTask `
        -TaskName $profileTaskName `
        -EncodedCommand $profileEncoded `
        -Description "Profile review watch persistant EZStudioLab Assistant"
}

Write-Output "EZS_ASSISTANT_SUPERVISION_START_OK"
