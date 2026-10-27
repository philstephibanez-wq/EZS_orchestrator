param([ValidateSet('preflight','start','status','maintenance','normal','stop-prod')][string]$Action='preflight')
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$php='H:\PHP\php-8.5-x64\php.exe'
$caddy='H:\Caddy\caddy.exe'
$dev=Join-Path $PSScriptRoot 'v2_lifecycle.ps1'
$prod=Join-Path $PSScriptRoot 'prod_lifecycle.ps1'
function CheckExit([string]$label) { if($LASTEXITCODE -ne 0){throw "EZS_RESTORE_PREFLIGHT_FAILED:$label"} }
function CheckFile([string]$path) {
    $tokens=$null;$errors=$null
    [Management.Automation.Language.Parser]::ParseFile($path,[ref]$tokens,[ref]$errors) | Out-Null
    if($errors.Count -gt 0){throw "EZS_RESTORE_PS_SYNTAX_FAILED:$path"}
}
if($Action -eq 'preflight' -or $Action -eq 'start') {
    CheckFile $dev
    CheckFile $prod
    CheckFile $PSCommandPath
    & $php (Join-Path $root 'tests\SymfonyV2LifecycleStaticContractTest.php');CheckExit 'DEV_CONTRACT'
    & $php (Join-Path $root 'tests\ProdLifecycleContractTest.php');CheckExit 'PROD_CONTRACT'
    & $php (Join-Path $root 'tests\SymfonyLegacyWebRetirementGateTest.php');CheckExit 'ROOT_CONTRACT'
    & $caddy validate --config (Join-Path $root 'config\caddy\Caddyfile.dev') --adapter caddyfile | Out-Null;CheckExit 'DEV_CADDY'
    & $caddy validate --config (Join-Path $root 'config\caddy\Caddyfile.prod') --adapter caddyfile | Out-Null;CheckExit 'PROD_CADDY'
    & $caddy validate --config (Join-Path $root 'config\caddy\Caddyfile.prod-internal-candidate') --adapter caddyfile | Out-Null;CheckExit 'PROD_INTERNAL'
    Write-Host 'EZS_RESTORE_PREFLIGHT_OK'
}
if($Action -eq 'preflight'){return}
if($Action -eq 'start') {
    $devStatus=(& $dev -Action status | Out-String)
    if($devStatus -notmatch 'state_present=True'){
        & $dev -Action start
    } elseif($devStatus -notmatch 'php_owned=True caddy_owned=True state_present=True'){
        throw 'EZS_RESTORE_REFUSED_DEV_STATE_NOT_OWNED'
    }
    $prodStatus=(& $prod -Action status | Out-String)
    if($prodStatus -notmatch 'state_present=True'){
        & $prod -Action start
    } elseif($prodStatus -notmatch 'ready=True'){
        throw 'EZS_RESTORE_REFUSED_PROD_STATE_NOT_OWNED'
    }
    & $dev -Action status
    & $prod -Action status
    Write-Host 'EZS_RESTORE_START_READY_PROD_IN_MAINTENANCE'
    return
}
if($Action -eq 'status') { & $dev -Action status; & $prod -Action status;return }
switch($Action) {
    'maintenance' { & $prod -Action maintenance }
    'normal' { & $prod -Action normal }
    'stop-prod' { & $prod -Action stop }
}
