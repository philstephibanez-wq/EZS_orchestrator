param([Parameter(Mandatory=$true)][ValidateSet('start','stop','status')][string]$Action)
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
    if ($Action -eq 'status') {
        if ($null -eq $state) { Write-Host 'EZS_V2_STOPPED'; exit 0 }
        $phpOwned = Owner ([int]$state.php_pid) 'php'
        $caddyOwned = Owner ([int]$state.caddy_pid) 'caddy'
        Write-Host "PHP_OWNED=$([bool]$phpOwned) CADDY_OWNED=$([bool]$caddyOwned) HTTP_8790=$([bool](Listener 8790))"
        exit 0
    }
    if ($Action -eq 'stop') {
        if ($null -eq $state) { Write-Host 'EZS_V2_NOT_OWNED'; exit 0 }
        foreach ($item in @(@('caddy','caddy_pid'),@('php','php_pid'))) {
            $pidValue = [int]$state.($item[1])
            $owned = Owner $pidValue $item[0]
            if ($null -ne $owned) { Stop-Process -Id $pidValue -Force -ErrorAction Stop }
            elseif ($null -ne (Get-Process -Id $pidValue -ErrorAction SilentlyContinue)) {
                throw "PID $pidValue non conforme : arret refuse, metadata conservees."
            }
        }
        Remove-Item -LiteralPath $Metadata -Force
        Write-Host 'EZS_V2_STOPPED'
        exit 0
    }
    if ($null -ne $state) {
        $existingPhp = Owner ([int]$state.php_pid) 'php'
        $existingCaddy = Owner ([int]$state.caddy_pid) 'caddy'
        if ($null -ne $existingPhp -and $null -ne $existingCaddy) {
            Write-Host 'EZS_V2_ALREADY_RUNNING'
            exit 0
        }
        throw 'Etat V2 partiel ou orphelin : utiliser status/stop et verifier les processus avant relance.'
    }
    foreach ($port in @(8790,8791)) {
        if ($null -ne (Listener $port)) { throw "Port $port deja occupe : demarrage refuse." }
    }
    if (Get-CimInstance Win32_Process -Filter "Name = 'caddy.exe'" -ErrorAction SilentlyContinue) {
        throw 'Caddy deja actif : ne pas creer une seconde instance DEV.'
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
        $caddyProcess = Start-Process -FilePath $CaddyExe -ArgumentList @('run','--config',('"' + $Caddyfile + '"'),'--adapter','caddyfile') -WorkingDirectory $Root -WindowStyle Hidden -PassThru
        if (-not (AwaitListener 8790)) { throw 'Caddy ne repond pas sur 8790.' }
        $response = Invoke-WebRequest -Uri 'http://127.0.0.1:8790/api/v2/environments' -UseBasicParsing -TimeoutSec 10
        if ($response.StatusCode -ne 200) { throw 'HTTP Symfony non valide.' }
        $payload = @{schema='ezs.v2-dev.lifecycle.v1';php_pid=$phpProcess.Id;caddy_pid=$caddyProcess.Id;started_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json
        [System.IO.File]::WriteAllText($Metadata, $payload + "`n", [System.Text.UTF8Encoding]::new($false))
        Write-Host 'EZS_V2_STARTED http://127.0.0.1:8790/'
    } catch {
        if ($null -ne $caddyProcess -and $null -ne (Owner ([int]$caddyProcess.Id) 'caddy')) { Stop-Process -Id $caddyProcess.Id -Force -ErrorAction SilentlyContinue }
        if ($null -ne $phpProcess -and $null -ne (Owner ([int]$phpProcess.Id) 'php')) { Stop-Process -Id $phpProcess.Id -Force -ErrorAction SilentlyContinue }
        throw
    }
} finally {
    $mutex.Dispose()
}
