<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$names=['QueueRestRead42C27ContractTest.php','QueueEventStream42C28ContractTest.php','ProdStatusBadge42C29ContractTest.php'];
foreach($names as $name){
 $source=(string)file_get_contents($root.'/tests/'.$name);
 if(!str_contains($source,"preg_match('/^4\\\\.2c(") && !str_contains($source,"preg_match('/^4\\.2c("))throw new RuntimeException('VERSION_GUARD_NOT_FUTURE_PROOF: '.$name);
}
echo "EZS_NO_FROZEN_QUEUE_UI_VERSION_GATES_4_2C31_OK\n";
