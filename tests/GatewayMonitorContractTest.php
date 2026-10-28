<?php
declare(strict_types=1);
$s=(string)file_get_contents(dirname(__DIR__).'/bin/gateway_monitor.php');
foreach(['READ_ONLY','safe_to_cutover','WindowsPortOwnership::snapshot','EZS_GATEWAY_MONITOR_ALERT','sleep($interval)','protocol_valid'] as $needle)
 if(!str_contains($s,$needle))throw new RuntimeException('GATEWAY_MONITOR_CONTRACT_MISSING:'.$needle);
foreach(['proc_terminate','Stop-Process','taskkill','unlink(','file_put_contents('] as $needle)
 if(str_contains($s,$needle))throw new RuntimeException('GATEWAY_MONITOR_MUTATION_FORBIDDEN:'.$needle);
echo "EZS_GATEWAY_MONITOR_CONTRACT_OK\n";
