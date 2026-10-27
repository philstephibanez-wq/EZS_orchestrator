param([Parameter(Mandatory=$true)][ValidateSet('start','status')][string]$Action)
$ErrorActionPreference='Stop'
$Root=Split-Path -Parent $PSScriptRoot
$Dir=Join-Path $Root 'runtime\caddy-dev'
$Meta=Join-Path $Dir 'instance.json'
$Lock=Join-Path $Dir 'instance.lock'
$Old=Join-Path $Root 'runtime\v2-dev\processes.json'
$Exe='H:\Caddy\caddy.exe'
$Config=Join-Path $Root 'web\config\caddy\Caddyfile.dev-preflight'
New-Item -ItemType Directory -Force -Path $Dir | Out-Null
$mutex=[IO.File]::Open($Lock,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
try {
 function Read-State([string]$Path) { if(!(Test-Path -LiteralPath $Path)){return $null}; try {return Get-Content -LiteralPath $Path -Raw -Encoding UTF8 | ConvertFrom-Json} catch {throw 'INVALID_METADATA'} }
 function Port([int]$Number) { $x=Get-NetTCPConnection -State Listen -LocalAddress 127.0.0.1 -LocalPort $Number -ErrorAction SilentlyContinue | Select-Object -First 1; if($x){return [int]$x.OwningProcess}; return 0 }
 function Identity([int]$Candidate) { if($Candidate -le 0){return $false}; $p=Get-CimInstance Win32_Process -Filter "ProcessId = $Candidate" -ErrorAction SilentlyContinue; if(!$p){return $false}; if(![string]::Equals([string]$p.ExecutablePath,$Exe,[StringComparison]::OrdinalIgnoreCase)){return $false}; return ([string]$p.CommandLine -match '(?:^|\s)run(?:\s|$)' -and [string]$p.CommandLine -match 'Caddyfile\.dev-preflight') }
 $state=Read-State $Meta; $previous=Read-State $Old
 $own=if($state){[int]$state.pid}else{0}; $legacy=if($previous){[int]$previous.caddy_pid}else{0}
 $a=Port 8790; $b=Port 8852
 if($a -gt 0 -and $a -eq $b -and (Identity $a) -and ($a -eq $own -or $a -eq $legacy)) { Write-Output "CADDY_DEV_REUSED PID=$a"; return }
 if($Action -eq 'status') { if($a -or $b){Write-Output "CADDY_DEV_UNKNOWN PORTS=$a,$b"}else{Write-Output 'CADDY_DEV_ABSENT'}; return }
 if($state -or $a -or $b -or ($legacy -and (Identity $legacy))){throw 'CADDY_DEV_CONFLICT'}
 foreach($f in @($Exe,$Config)){if(!(Test-Path -LiteralPath $f -PathType Leaf)){throw "MISSING $f"}}
 & $Exe validate --config $Config --adapter caddyfile
 if($LASTEXITCODE -ne 0){throw 'CADDY_CONFIG_INVALID'}
 $p=Start-Process -FilePath $Exe -ArgumentList @('run','--config',('"'+$Config+'"'),'--adapter','caddyfile') -WorkingDirectory $Root -PassThru -WindowStyle Hidden
 try { $ready=$false; for($i=0;$i -lt 40;$i++){Start-Sleep -Milliseconds 250; if((Port 8790) -eq $p.Id -and (Port 8852) -eq $p.Id -and (Identity $p.Id)){$ready=$true;break};if($p.HasExited){break}}; if(!$ready){throw 'CADDY_DEV_NOT_READY'}
 $json=@{schema='ezs.caddy-dev.v1';pid=$p.Id}|ConvertTo-Json;[IO.File]::WriteAllText($Meta,$json+"`n",[Text.UTF8Encoding]::new($false));Write-Output "CADDY_DEV_STARTED PID=$($p.Id)"
 }catch{if(Identity $p.Id){Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue};throw}
}finally{$mutex.Dispose()}
