<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
$a=strpos($s,'function WaitOwned([int]$port,[int]$processId)');
$b=strpos($s,'function HttpStatus',$a);
if($a===false||$b===false)throw new RuntimeException('WAITOWNED_MISSING');
$x=substr($s,$a,$b-$a);
foreach(['Dev-TcpReachable $port','Get-CimInstance Win32_Process','ExecutablePath','-b 127.0.0.1:$port'] as $token){if(!str_contains($x,$token))throw new RuntimeException('MISSING_'.$token);}
if(str_contains($x,'@(Owners $port)'))throw new RuntimeException('OLD_TCP_GUARD');
if(!str_contains($s,'if(-not(IsOwned $target.port $target.processId $target.stamp))'))throw new RuntimeException('REFRESH_GUARD');
echo "EZS_DEV_WAITOWNED_4_2C43_OK\n";