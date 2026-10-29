<?php
declare(strict_types=1);
foreach (['start.ps1','stop.ps1'] as $file) {
 $s=(string)file_get_contents(dirname(__DIR__).'/scripts/'.$file);
 $a=strpos($s,'function Invoke-EzsProdLifecycle');
 $b=strpos($s,"\n\$ErrorActionPreference='Stop'\n\$root=",$a+500);
 if($a===false || $b===false)throw new RuntimeException('PROD_HELPER_MISSING '.$file);
 $p=substr($s,$a,$b-$a);
 foreach (['prod_gateway_php\\router.php','Caddyfile.gateway-php-prod','18515','ezs.prod.php.v1','EZS_PROD_START_MAINTENANCE_OK'] as $token)if(!str_contains($p,$token))throw new RuntimeException('MISSING '.$token.' '.$file);
 foreach (['python.exe','server.py','prod_gateway\\server.py'] as $forbidden)if(str_contains($p,$forbidden))throw new RuntimeException('LEGACY_PYTHON '.$file);
}
echo "EZS_PROD_PHP_ONLY_4_2C48_OK\n";