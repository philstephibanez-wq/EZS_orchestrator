<?php
declare(strict_types=1);
$root=dirname(__DIR__);
$checks=[
 'config/caddy/Caddyfile.prod-internal-candidate',
 'src/Module/Infrastructure/ProdFastcgiPreflight.php',
 'src/Module/Infrastructure/Controller/ProdOperationsController.php',
 'composer.json','composer.lock','bin/console'
];
foreach($checks as $file){if(!is_file($root.'/'.$file))throw new RuntimeException('MISSING_ROOT_FILE:'.$file);}
$preflight=(string)file_get_contents($root.'/src/Module/Infrastructure/ProdFastcgiPreflight.php');
if(!str_contains($preflight, "/config/caddy/Caddyfile.prod-internal-candidate"))throw new RuntimeException('PREFLIGHT_NOT_ROOTED');
if(str_contains($preflight, "/web/config/caddy/"))throw new RuntimeException('PREFLIGHT_LEGACY_WEB_PATH');
$prod=(string)file_get_contents($root.'/src/Module/Infrastructure/Controller/ProdOperationsController.php');
if(str_contains($prod, 'python.exe')||str_contains($prod, 'new Process('))throw new RuntimeException('ROOT_PROD_USES_LEGACY_EXECUTOR');
if(!str_contains($prod, 'prod_lifecycle_migration_pending'))throw new RuntimeException('PROD_NOT_FAIL_CLOSED');
$composer=json_decode((string)file_get_contents($root.'/composer.json'),true,512,JSON_THROW_ON_ERROR);
if(($composer['name']??null)!=='ezs/orchestrator')throw new RuntimeException('COMPOSER_ROOT_NAME');
echo "SYMFONY_ROOT_RUNTIME_CONTRACT_OK\n";
