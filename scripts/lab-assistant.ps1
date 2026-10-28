param([ValidateSet('preflight','start','status')][string]$Action='preflight')
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$caddy='H:\Caddy\caddy.exe'
$config=Join-Path $root 'config\caddy\Caddyfile.dev-lab-assistant-candidate'
$php='H:\PHP\php-8.5-x64\php-cgi.exe'
$runtime=Join-Path $root 'runtime\v2-dev'
$lockPath=Join-Path $runtime 'lab-assistant.lock'
$statePath=Join-Path $runtime 'lab-assistant.json'
$targets=@(
    @{name='LAB';root='H:\EZStudio_lab';port=8701},
    @{name='ASSISTANT';root='H:\EZStudioLab_assistant';port=8713}
)
function Listener([int]$port){
    return @(Get-NetTCPConnection -LocalAddress '127.0.0.1' -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}
function Attested([int]$port,[int]$processId,[string]$stamp){
    if($processId -le 0 -or -not $stamp){return $false}
    $p=Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
    $l=@(Listener $port)
    if($null -eq $p -or $l.Count -ne 1 -or [int]$l[0].OwningProcess -ne $processId){return $false}
    if(-not [string]::Equals([string]$p.ExecutablePath,$php,[StringComparison]::OrdinalIgnoreCase)){return $false}
    if(-not ([string]$p.CommandLine).Contains("-b 127.0.0.1:$port")){return $false}
    try{return ([datetime]$p.CreationDate).ToUniversalTime().ToString('o') -eq $stamp}catch{return $false}
}
foreach($path in @($php,$caddy,$config)){
    if(-not(Test-Path -LiteralPath $path -PathType Leaf)){throw "EZS_LA_DEPENDENCY_MISSING:$path"}
}
foreach($target in $targets){
    foreach($relative in @('public\index.php','vendor\autoload_runtime.php')){
        if(-not(Test-Path -LiteralPath (Join-Path $target.root $relative) -PathType Leaf)){
            throw "EZS_LA_DEPENDENCY_MISSING:$($target.name):$relative"
        }
    }
}
& $caddy validate --config $config --adapter caddyfile | Out-Null
if($LASTEXITCODE -ne 0){throw 'EZS_LA_CADDY_CANDIDATE_INVALID'}
if($Action -eq 'preflight'){
    Write-Host 'EZS_LA_PREFLIGHT_OK_CANDIDATE_NOT_APPLIED'
    return
}
New-Item -ItemType Directory -Force -Path $runtime | Out-Null
$lock=$null
try{$lock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)}
catch{throw 'EZS_LA_CONCURRENT_OPERATION'}
try{
    if(Test-Path -LiteralPath $statePath){
        $state=Get-Content -LiteralPath $statePath -Raw -Encoding UTF8 | ConvertFrom-Json
        if($state.schema -ne 'ezs.la.backends.v1'){throw 'EZS_LA_STATE_INVALID'}
        foreach($t in $targets){
            $entry=if($t.name -eq 'LAB'){$state.lab}else{$state.assistant}
            if(-not(Attested $t.port ([int]$entry.pid) ([string]$entry.stamp))){
                throw "EZS_LA_STALE_OR_FOREIGN_STATE:$($t.name)"
            }
        }
        Write-Host 'EZS_LA_BACKENDS_ALREADY_RUNNING_VERIFIED'
        return
    }
    if($Action -eq 'status'){
        foreach($t in $targets){Write-Host "EZS_LA_UNMANAGED port=$($t.port) listeners=$(@(Listener $t.port).Count)"}
        return
    }
    foreach($t in $targets){
        if(@(Listener $t.port).Count -gt 0){throw "EZS_LA_REFUSED_UNOWNED_PORT_$($t.port)"}
    }
    $started=@()
    try{
        foreach($t in $targets){
            $env:APP_ENV='dev';$env:APP_DEBUG='1';$env:PHP_FCGI_MAX_REQUESTS='0'
            $p=Start-Process -FilePath $php -ArgumentList "-b 127.0.0.1:$($t.port)" -WorkingDirectory $t.root -WindowStyle Hidden -PassThru
            $started+=@{port=$t.port;pid=[int]$p.Id}
            $ready=$false
            for($i=0;$i -lt 40;$i++){
                $l=@(Listener $t.port)
                if($l.Count -eq 1 -and [int]$l[0].OwningProcess -eq [int]$p.Id){$ready=$true;break}
                if($p.HasExited){break}
                Start-Sleep -Milliseconds 250
            }
            if(-not $ready){throw "EZS_LA_START_FAILED_$($t.port)"}
        }
        $records=@()
        foreach($p in $started){
            $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$($p.pid)"
            if($null -eq $proc){throw 'EZS_LA_START_PROCESS_GONE'}
            $stamp=([datetime]$proc.CreationDate).ToUniversalTime().ToString('o')
            if(-not(Attested $p.port $p.pid $stamp)){throw 'EZS_LA_START_NOT_ATTESTED'}
            $records+=@{pid=$p.pid;stamp=$stamp}
        }
        $state=[ordered]@{schema='ezs.la.backends.v1';lab=$records[0];assistant=$records[1]}
        [IO.File]::WriteAllText($statePath,($state|ConvertTo-Json -Depth 5),[Text.UTF8Encoding]::new($false))
        Write-Host 'EZS_LA_BACKENDS_READY_8701_8713_CADDY_CANDIDATE_STILL_INACTIVE'
    }catch{
        foreach($p in $started){
            $proc=Get-CimInstance Win32_Process -Filter "ProcessId=$($p.pid)" -ErrorAction SilentlyContinue
            if($null -ne $proc -and [string]::Equals([string]$proc.ExecutablePath,$php,[StringComparison]::OrdinalIgnoreCase) -and ([string]$proc.CommandLine).Contains("-b 127.0.0.1:$($p.port)")){
                Stop-Process -Id $p.pid -ErrorAction SilentlyContinue
            }
        }
        throw
    }
}finally{if($null -ne $lock){$lock.Dispose()}}
