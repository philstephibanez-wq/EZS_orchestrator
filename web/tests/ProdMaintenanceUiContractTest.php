<?php
declare(strict_types=1);
$root=dirname(__DIR__,2);
$p=file_get_contents($root.'/web/src/Module/Infrastructure/Controller/ProdOperationsController.php');
$t=file_get_contents($root.'/web/templates/infrastructure/index.html.twig');
$j=file_get_contents($root.'/web/public/assets/ezs-prod-control.js');
foreach(['methods:[\'POST\']','X-EZS-CSRF','invalid_origin','hash_equals','set_maintenance(True)','audit.log'] as $needle) if(!str_contains($p,$needle))throw new RuntimeException('missing '.$needle);
if(str_contains($p,'set_maintenance(False)')||str_contains($p,'servers.start('))throw new RuntimeException('unsafe change');
foreach(['prod-maintenance-button','ezs-prod-control.js','prod-maintenance','prod-caddy'] as $needle)if(!str_contains($t,$needle))throw new RuntimeException('missing ui '.$needle);
if(!str_contains($j,'window.confirm'))throw new RuntimeException('confirmation missing');
echo "EZS_PROD_MAINTENANCE_UI_CONTRACT_OK\n";
