param([Parameter(Mandatory=$true)][ValidateSet('start','stop','status')][string]$Action)
$ErrorActionPreference = 'Stop'
$Root = Split-Path -Parent $PSScriptRoot
$Runtime = Join-Path $Root 'runtime\v2-dev'
$StateFile = Join-Path $Runtime 'ezscore-preview.json'
$LockFile = Join-Path $Runtime 'ezscore-preview.lock'
$Exe = 'H:\PHP\php-8.5-x64\php-cgi.exe'
$App = 'H:\EZScore_dev'
$Port = 8862
New-Item -ItemType Directory -Force -Path $Runtime | Out-Null
$lock = [System.IO.File]::Open($LockFile,[System.IO.FileMode]::OpenOrCreate,[System.IO.FileAccess]::ReadWrite,[System.IO.FileShare]::None)
try {
    function Owned($processId) {
        if (-not $processId -or [int]$processId -lt 1) { return $false }
        $p = Get-CimInstance Win32_Process -Filter "ProcessId = $([int]$processId)" -ErrorAction SilentlyContinue
        if (-not $p) { return $false }
        if (-not [string]::Equals([string]$p.ExecutablePath,$Exe,[System.StringComparison]::OrdinalIgnoreCase)) { return $false }
        return [string]$p.CommandLine -match '(?:^|\s)-b\s+127\.0\.0\.1:8862(?:\s|$)'
    }
    function Listener { return Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1 }
    $state = $null
    if (Test-Path -LiteralPath $StateFile) {
        try { $state = Get-Content -LiteralPath $StateFile -Raw -Encoding UTF8 | ConvertFrom-Json }
        catch { throw 'Métadonnées DEV illisibles : opération refusée.' }
    }
    if ($Action -eq 'status') {
        if ($null -eq $state) {
            Write-Host "EZScore_PREVIEW_UNMANAGED TCP=$([bool](Listener))"
        } else {
            Write-Host "EZScore_PREVIEW_OWNED=$(Owned $state.pid) PID=$($state.pid) TCP=$([bool](Listener))"
        }
    } elseif ($Action -eq 'stop') {
        if ($null -eq $state) { Write-Host 'EZScore_PREVIEW_NOT_OWNED'; return }
        if (Owned $state.pid) {
            $listener = Listener
            if (-not $listener -or [int]$listener.OwningProcess -ne [int]$state.pid) { throw 'Écoute et PID incohérents : arrêt refusé.' }
            Stop-Process -Id ([int]$state.pid) -Force -ErrorAction Stop
        } elseif (Get-Process -Id ([int]$state.pid) -ErrorAction SilentlyContinue) {
            throw 'PID réutilisé ou étranger : arrêt refusé.'
        }
        Remove-Item -LiteralPath $StateFile -Force
        Write-Host 'EZScore_PREVIEW_STOPPED'
    } else {
        if ($state) {
            if ((Owned $state.pid) -and (Listener)) { Write-Host 'EZScore_PREVIEW_ALREADY_RUNNING'; return }
            throw 'État préflight incohérent : démarrage refusé.'
        }
        if (Listener) { throw "Port $Port déjà occupé : démarrage refusé." }
        foreach ($path in @($Exe,(Join-Path $App 'public\index.php'),(Join-Path $App 'vendor\autoload.php'))) {
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Dépendance absente : $path" }
        }
        $env:APP_ENV = 'dev'
        $env:APP_DEBUG = '1'
        $p = Start-Process -FilePath $Exe -ArgumentList @('-b',"127.0.0.1:$Port") -WorkingDirectory $App -WindowStyle Hidden -PassThru
        try {
            $ready = $false
            for ($i=0;$i -lt 40;$i++) {
                Start-Sleep -Milliseconds 250
                $l = Listener
                if ($l -and [int]$l.OwningProcess -eq [int]$p.Id -and (Owned $p.Id)) { $ready=$true; break }
                if ($p.HasExited) { break }
            }
            if (-not $ready) { throw 'FastCGI DEV ne démarre pas ou PID non conforme.' }
            $json = @{schema='ezs.dev-preview.v1'; pid=$p.Id; port=$Port; started_utc=[DateTime]::UtcNow.ToString('o')} | ConvertTo-Json
            [System.IO.File]::WriteAllText($StateFile,$json+"`n",[System.Text.UTF8Encoding]::new($false))
            Write-Host "EZScore_PREVIEW_STARTED PID=$($p.Id) 127.0.0.1:$Port (FastCGI)"
        } catch {
            if (Owned $p.Id) { Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue }
            throw
        }
    }
} finally { $lock.Dispose() }
