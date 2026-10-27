<?php
$c=file_get_contents(__DIR__.'/../config/caddy/Caddyfile.prod');
$i=file_get_contents(__DIR__.'/../config/caddy/Caddyfile.prod-internal-candidate');
foreach ([[$c,8501],[$i,8511]] as [$s,$port]) {
 if(strpos($s,':'.$port.' {')===false || strpos($s,'bind 127.0.0.1')===false || strpos($s,'http://127.0.0.1:'.$port.' {')!==false) throw new RuntimeException('PROD_HOST_MATCH_FAILED_'.$port);
}
$ui=file_get_contents(__DIR__.'/../templates/infrastructure/index.html.twig');
$ctrl=file_get_contents(__DIR__.'/../src/Module/Infrastructure/Controller/ProdOperationsController.php');
if(strpos($ui,'id="prod-normal-button"')===false || strpos($ctrl,"'normal'=>\$backend")===false) throw new RuntimeException('PROD_NORMAL_UI_NOT_CONNECTED');
echo "EZS_PROD_UI_AND_HOST_CONTRACT_OK\n";
