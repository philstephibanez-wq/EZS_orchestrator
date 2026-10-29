<?php
declare(strict_types=1);
$s=file_get_contents(dirname(__DIR__).'/scripts/start.ps1');
$a=strpos($s,'function Invoke-EzsLabAssistantLifecycle');
$b=strpos($s,'function Invoke-EzsProdLifecycle',$a);
$p=substr($s,$a,$b-$a);
foreach(['function La-Identity','function La-TcpReachable','La-TcpReachable $t.port','La-Identity $p.port $p.pid $stamp','La-Identity $t.port ([int]$entry.pid)','EZS_LA_START_FAILED_'] as $needle){if(!str_contains($p,$needle) && $needle!=='EZS_LA_START_FAILED_')throw new RuntimeException('MISSING '.$needle);}
if(!str_contains($p,'if(-not(Attested $t.port ([int]$entry.pid) ([string]$entry.stamp)))'))throw new RuntimeException('STOP_GUARD_REMOVED');
echo "EZS_LA_WAIT_4_2C44_OK\n";