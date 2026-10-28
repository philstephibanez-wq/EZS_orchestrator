<?php
declare(strict_types=1);
// Durable native PHP CLI entry for verified PROD mode changes.
// Usage: php bin/prod_mode.php maintenance | normal | status
$action=$argv[1]??'status';
if(!in_array($action,['maintenance','normal','status'],true)){
 fwrite(STDERR,"EZS_PROD_MODE_INVALID_ACTION\n");exit(2);
}
require_once dirname(__DIR__).'/src/Module/Infrastructure/ProdModeService.php';
try {
 $service=new \Ezs\Web\Module\Infrastructure\ProdModeService();
 $result=$action==='status'?$service->inspect():$service->apply($action);
 echo json_encode($result,JSON_PRETTY_PRINT|JSON_UNESCAPED_SLASHES|JSON_THROW_ON_ERROR)."\n";
 if($action==='status' && ($result['gateway_online']??false)!==true)exit(1);
} catch(Throwable $e){
 fwrite(STDERR,"EZS_PROD_MODE_FAILED:".$e->getMessage()."\n");exit(1);
}
