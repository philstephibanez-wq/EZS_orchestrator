param(
    [Parameter(Mandatory=$true)][ValidateSet('start','stop','status','recover')][string]$Action,
    [int]$ExpectedPid = 0,
    [switch]$ConfirmRecovery
)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Web = Join-Path $Root 'web'
$Runtime = Join-Path $Root 'runtime\v2-dev'
$Metadata = Join-Path $Runtime 'processes.json'
$MutexFile = Join-Path $Runtime 'lifecycle.lock'
$PhpExe = 'H:\PHP\php-8.5-x64\php-cgi.exe'
$CaddyExe = 'H:\Caddy\caddy.exe'
$Caddyfile = Join-Path $Web 'config\caddy\Caddyfile.dev-preflight'

New-Item -ItemType Directory -Path $Runtime -Force | Out-Null
$mutex = [System.IO.File]::Open($MutexFile, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
try {
    function Owner([int]$Id, [string]$Kind) {
        if ($Id -le 0) { return $null }
        $process = Get-CimInstance Win32_Process -Filter "ProcessId = $Id" -ErrorAction SilentlyContinue
        if ($null -eq $process) { return $null }
        $expected = if ($Kind -eq 'php') { $PhpExe } else { $CaddyExe }
        if (-not [string]::Equals([string]$process.ExecutablePath, $expected, [System.StringComparison]::OrdinalIgnoreCase)) { return $null }
        $command = [string]$process.CommandLine
        if ($Kind -eq 'php' -and ($command -notmatch ' -b 127\.0\.0\.1:8791')) { return $null }
        if ($Kind -eq 'caddy' -and ($command -notmatch 'Caddyfile\.dev-preflight' -or $command -notmatch ' run ')) { return $null }
        return $process
    }
    function Listener([int]$Port) {
        return Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Select-Object -First 1
    }
    function AwaitListener([int]$Port) {
        for ($i = 0; $i -lt 40; $i++) {
            if ($null -ne (Listener $Port)) { return $true }
            Start-Sleep -Milliseconds 250
        }
        return $false
    }
    $state = $null
    if (Test-Path -LiteralPath $Metadata) {
        try { $state = Get-Content -LiteralPath $Metadata -Raw -Encoding UTF8 | ConvertFrom-Json }
        catch { throw 'Metadata V2 invalide : aucun processus ne sera modifie.' }
    }
    if ($Action -eq 'recover') {
        if (-not $ConfirmRecovery -or $ExpectedPid -le 0) {
            throw 'RECOVERY_REQUIRES_EXPECTED_PID_AND_EXPLICIT_CONFIRMATION'
        }
        if ($null -eq $state -or [int]$state.php_pid -ne 0) {
            throw 'RECOVERY_REQUIRES_STOPPED_METADATA'
        }
        $caddyPid = [int]$state.caddy_pid
        $caddyListener = Listener 8790
        if ($null -eq $caddyListener -or [int]$caddyListener.OwningProcess -ne $caddyPid -or
            $null -eq (Owner $caddyPid 'caddy')) {
            throw 'RECOVERY_CADDY_IDENTITY_MISMATCH'
        }
        $backendListener = Listener 8791
        if ($null -eq $backendListener -or [int]$backendListener.OwningProcess -ne $ExpectedPid -or
            $null -eq (Owner $ExpectedPid 'php')) {
            throw 'RECOVERY_BACKEND_IDENTITY_MISMATCH'
        }
        $backend = Get-CimInstance Win32_Process -Filter "ProcessId = $ExpectedPid" -ErrorAction Stop
        if ([string]$backend.CommandLine -notmatch '(?i)^"?(?:H:\\PHP\\php-8\.5-x64\\php-cgi\.exe)"?\s+-b\s+127\.0\.0\.1:8791\s*
        if ($null -eq $state) { Write-Host 'EZS_V2_STOPPED'; exit 0 }
        $phpOwned = Owner ([int]$state.php_pid) 'php'
        $caddyOwned = Owner ([int]$state.caddy_pid) 'caddy'
        $listener8791 = Listener 8791
        $backendPid = if ($listener8791) { [int]$listener8791.OwningProcess } else { 0 }
        $phpPid = [int]$state.php_pid
        $ownershipMismatch = ($backendPid -gt 0 -and ($phpPid -ne $backendPid -or -not $phpOwned))
        Write-Host "PHP_OWNED=$([bool]$phpOwned) CADDY_OWNED=$([bool]$caddyOwned) HTTP_8790=$([bool](Listener 8790)) BACKEND_PID=$backendPid OWNERSHIP_MISMATCH=$ownershipMismatch"
        exit 0
    }
    if ($Action -eq 'stop') {
        if ($null -eq $state) { Write-Host 'EZS_V2_NOT_OWNED'; exit 0 }
        foreach ($item in @(@('php','php_pid'))) {
            $pidValue = [int]$state.($item[1])
            if ($pidValue -eq 0) { continue }
            if ($pidValue -lt 0) { throw 'PID PHP invalide : arrêt refusé.' }
            $owned = Owner $pidValue $item[0]
            if ($null -ne $owned) { Stop-Process -Id $pidValue -Force -ErrorAction Stop }
            elseif ($null -ne (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)) {
                throw "PID $pidValue non conforme : arret refuse, metadata conservees."
            }
        }
        $remaining = Listener 8791
        if ($null -ne $remaining) {
            $remainingPid = [int]$remaining.OwningProcess
            throw "BACKEND_8791_STILL_LISTENING PID=$remainingPid : metadata preserved, Caddy untouched."
        }
        $state.php_pid = 0
        [System.IO.File]::WriteAllText($Metadata,($state | ConvertTo-Json) + "`n",[System.Text.UTF8Encoding]::new($false))
        Write-Host 'EZS_V2_STOPPED_CADDY_PRESERVED'
        exit 0
    }
    if ($null -ne $state) {
        $existingPhp = Owner ([int]$state.php_pid) 'php'
        $bound8791 = Listener 8791
        if ($existingPhp -and $bound8791 -and [int]$bound8791.OwningProcess -eq [int]$state.php_pid) { Write-Host 'EZS_V2_ALREADY_RUNNING'; exit 0 }
        if ($existingPhp -or (([int]$state.php_pid -gt 0) -and (Get-Process -Id ([int]$state.php_pid) -ErrorAction SilentlyContinue))) { throw 'PID PHP ambigu : demarrage refuse.' }
    }
    foreach ($port in @(8791)) {
        if ($null -ne (Listener $port)) { throw "Port $port deja occupe : demarrage refuse." }
    }
    foreach ($path in @($PhpExe,$CaddyExe,$Caddyfile,(Join-Path $Web 'vendor\autoload.php'))) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Dependance absente: $path" }
    }
    $env:APP_ENV = 'dev'
    $env:APP_DEBUG = '1'
    if (-not $env:APP_SECRET) { $env:APP_SECRET = [guid]::NewGuid().ToString('N') }
    $phpProcess = $null
    $caddyProcess = $null
    try {
        $phpProcess = Start-Process -FilePath $PhpExe -ArgumentList @('-b','127.0.0.1:8791') -WorkingDirectory $Web -WindowStyle Hidden -PassThru
        if (-not (AwaitListener 8791)) { throw 'PHP FastCGI ne repond pas sur 8791.' }
        $listenerPid = [int](Listener 8791).OwningProcess
        if ($listenerPid -ne [int]$phpProcess.Id -or $null -eq (Owner $listenerPid 'php')) {
            throw "BACKEND_8791_UNEXPECTED_PID=$listenerPid STARTED_PID=$($phpProcess.Id) : no adoption."
        }
        & (Join-Path $PSScriptRoot 'caddy_dev_shared.ps1') -Action start
        if (-not (AwaitListener 8790)) { throw 'Caddy DEV indisponible.' }
        $caddyPid = [int](Listener 8790).OwningProcess
        if ($null -eq (Owner $caddyPid 'caddy')) { throw 'Identite Caddy DEV incorrecte.' }
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8790/api/v2/environments' -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -ne 200) { throw 'HTTP Symfony non valide.' }
        $payload = @{schema='ezs.v2-dev.lifecycle.v1';php_pid=$phpProcess.Id;caddy_pid=$caddyPid;started_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json
        [System.IO.File]::WriteAllText($Metadata, $payload + "`n", [System.Text.UTF8Encoding]::new($false))
        Write-Host 'EZS_V2_STARTED http://127.0.0.1:8790/'
    } catch {
        if ($null -ne $phpProcess -and $null -ne (Owner ([int]$phpProcess.Id) 'php')) { Stop-Process -Id $phpProcess.Id -Force -ErrorAction SilentlyContinue }
        throw
    }
} finally {
    $mutex.Dispose()
}
) {
            throw 'RECOVERY_COMMANDLINE_NOT_EXACT'
        }
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8790/api/v2/environments' -UseBasicParsing -TimeoutSec 15
        if ($response.StatusCode -ne 200) { throw 'RECOVERY_HTTP_NOT_READY' }
        $secondListen = Listener 8791
        if ($null -eq $secondListen -or [int]$secondListen.OwningProcess -ne $ExpectedPid -or
            $null -eq (Owner $ExpectedPid 'php')) {
            throw 'RECOVERY_PID_CHANGED'
        }
        $state.php_pid = $ExpectedPid
        $state | Add-Member -MemberType NoteProperty -Name recovered_utc -Value ([DateTime]::UtcNow.ToString('o')) -Force
        $state | Add-Member -MemberType NoteProperty -Name recovery_mode -Value 'operator_explicit_pid' -Force
        [System.IO.File]::WriteAllText($Metadata,($state | ConvertTo-Json) + "`n",[System.Text.UTF8Encoding]::new($false))
        Write-Host "EZS_V2_RECOVERED PID=$ExpectedPid CADDY_PID=$caddyPid"
        exit 0
    }
    if ($Action -eq 'status') {
        if ($null -eq $state) { Write-Host 'EZS_V2_STOPPED'; exit 0 }
        $phpOwned = Owner ([int]$state.php_pid) 'php'
        $caddyOwned = Owner ([int]$state.caddy_pid) 'caddy'
        $listener8791 = Listener 8791
        $backendPid = if ($listener8791) { [int]$listener8791.OwningProcess } else { 0 }
        $phpPid = [int]$state.php_pid
        $ownershipMismatch = ($backendPid -gt 0 -and ($phpPid -ne $backendPid -or -not $phpOwned))
        Write-Host "PHP_OWNED=$([bool]$phpOwned) CADDY_OWNED=$([bool]$caddyOwned) HTTP_8790=$([bool](Listener 8790)) BACKEND_PID=$backendPid OWNERSHIP_MISMATCH=$ownershipMismatch"
        exit 0
    }
    if ($Action -eq 'stop') {
        if ($null -eq $state) { Write-Host 'EZS_V2_NOT_OWNED'; exit 0 }
        foreach ($item in @(@('php','php_pid'))) {
            $pidValue = [int]$state.($item[1])
            if ($pidValue -eq 0) { continue }
            if ($pidValue -lt 0) { throw 'PID PHP invalide : arrêt refusé.' }
            $owned = Owner $pidValue $item[0]
            if ($null -ne $owned) { Stop-Process -Id $pidValue -Force -ErrorAction Stop }
            elseif ($null -ne (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)) {
                throw "PID $pidValue non conforme : arret refuse, metadata conservees."
            }
        }
        $remaining = Listener 8791
        if ($null -ne $remaining) {
            $remainingPid = [int]$remaining.OwningProcess
            throw "BACKEND_8791_STILL_LISTENING PID=$remainingPid : metadata preserved, Caddy untouched."
        }
        $state.php_pid = 0
        [System.IO.File]::WriteAllText($Metadata,($state | ConvertTo-Json) + "`n",[System.Text.UTF8Encoding]::new($false))
        Write-Host 'EZS_V2_STOPPED_CADDY_PRESERVED'
        exit 0
    }
    if ($null -ne $state) {
        $existingPhp = Owner ([int]$state.php_pid) 'php'
        $bound8791 = Listener 8791
        if ($existingPhp -and $bound8791 -and [int]$bound8791.OwningProcess -eq [int]$state.php_pid) { Write-Host 'EZS_V2_ALREADY_RUNNING'; exit 0 }
        if ($existingPhp -or (([int]$state.php_pid -gt 0) -and (Get-Process -Id ([int]$state.php_pid) -ErrorAction SilentlyContinue))) { throw 'PID PHP ambigu : demarrage refuse.' }
    }
    foreach ($port in @(8791)) {
        if ($null -ne (Listener $port)) { throw "Port $port deja occupe : demarrage refuse." }
    }
    foreach ($path in @($PhpExe,$CaddyExe,$Caddyfile,(Join-Path $Web 'vendor\autoload.php'))) {
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Dependance absente: $path" }
    }
    $env:APP_ENV = 'dev'
    $env:APP_DEBUG = '1'
    if (-not $env:APP_SECRET) { $env:APP_SECRET = [guid]::NewGuid().ToString('N') }
    $phpProcess = $null
    $caddyProcess = $null
    try {
        $phpProcess = Start-Process -FilePath $PhpExe -ArgumentList @('-b','127.0.0.1:8791') -WorkingDirectory $Web -WindowStyle Hidden -PassThru
        if (-not (AwaitListener 8791)) { throw 'PHP FastCGI ne repond pas sur 8791.' }
        $listenerPid = [int](Listener 8791).OwningProcess
        if ($listenerPid -ne [int]$phpProcess.Id -or $null -eq (Owner $listenerPid 'php')) {
            throw "BACKEND_8791_UNEXPECTED_PID=$listenerPid STARTED_PID=$($phpProcess.Id) : no adoption."
        }
        & (Join-Path $PSScriptRoot 'caddy_dev_shared.ps1') -Action start
        if (-not (AwaitListener 8790)) { throw 'Caddy DEV indisponible.' }
        $caddyPid = [int](Listener 8790).OwningProcess
        if ($null -eq (Owner $caddyPid 'caddy')) { throw 'Identite Caddy DEV incorrecte.' }
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8790/api/v2/environments' -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -ne 200) { throw 'HTTP Symfony non valide.' }
        $payload = @{schema='ezs.v2-dev.lifecycle.v1';php_pid=$phpProcess.Id;caddy_pid=$caddyPid;started_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json
        [System.IO.File]::WriteAllText($Metadata, $payload + "`n", [System.Text.UTF8Encoding]::new($false))
        Write-Host 'EZS_V2_STARTED http://127.0.0.1:8790/'
    } catch {
        if ($null -ne $phpProcess -and $null -ne (Owner ([int]$phpProcess.Id) 'php')) { Stop-Process -Id $phpProcess.Id -Force -ErrorAction SilentlyContinue }
        throw
    }
} finally {
    $mutex.Dispose()
}
