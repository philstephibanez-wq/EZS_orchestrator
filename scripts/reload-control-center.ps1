#Requires -Version 5.1
# Exact-owner reload of the Control Center HTTP service (port 8700).
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$ExpectedVersion)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$python='H:\Python\pythoncore-3.14-64\python.exe'
$metaPath=Join-Path $root 'runtime\control_center\instance.json'
$port=8700
function Owner {
    $net=Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -eq $net) { return 0 }
    return [int]$net.OwningProcess
}
$existing=Owner
if ($existing -ne 0) {
    if (-not (Test-Path -LiteralPath $metaPath -PathType Leaf)) { throw 'CONTROL_CENTER_OWNER_METADATA_MISSING' }
    $meta=Get-Content -LiteralPath $metaPath -Raw | ConvertFrom-Json
    if ([int]$meta.pid -ne $existing -or [int]$meta.port -ne $port) {
        throw 'CONTROL_CENTER_PID_NOT_OWNED'
    }
    $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$existing" -ErrorAction Stop
    if ($null -eq $proc -or $proc.Name -notin @('python.exe','pythonw.exe') -or
        $proc.CommandLine -notmatch 'control_center\.web') {
        throw 'CONTROL_CENTER_PROCESS_IDENTITY_UNVERIFIED'
    }
    Stop-Process -Id $existing -ErrorAction Stop
    $deadline=[DateTime]::UtcNow.AddSeconds(12)
    while ((Owner) -ne 0 -and [DateTime]::UtcNow -lt $deadline) {
        Start-Sleep -Milliseconds 250
    }
    if ((Owner) -ne 0) { throw 'CONTROL_CENTER_PORT_STILL_BUSY' }
}
$logDir=Join-Path $root 'runtime\control_center'
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$proc=Start-Process -FilePath $python -ArgumentList @('-m','control_center.web','--port','8700','--no-browser') -WorkingDirectory $root -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logDir 'web.out.log') -RedirectStandardError (Join-Path $logDir 'web.err.log')
$deadline=[DateTime]::UtcNow.AddSeconds(12)
$validated=$false
while ([DateTime]::UtcNow -lt $deadline) {
    if ($proc.HasExited) { throw "CONTROL_CENTER_EXITED:$($proc.ExitCode)" }
    if ((Owner) -eq $proc.Id) {
        try {
            $response=Invoke-WebRequest -Uri "http://127.0.0.1:$port/" -UseBasicParsing -TimeoutSec 3
            if ($response.StatusCode -eq 200 -and $response.Content.Contains("ORCHESTRATOR <span class=")) {
                if ($response.Content.Contains("V$ExpectedVersion</span>")) {
                    $validated=$true
                    break
                }
            }
        } catch {}
    }
    Start-Sleep -Milliseconds 350
}
if (-not $validated) { throw 'CONTROL_CENTER_RUNTIME_VERSION_NOT_CONFIRMED' }
Write-Output "CONTROL_CENTER_RELOADED version=$ExpectedVersion pid=$($proc.Id)"
