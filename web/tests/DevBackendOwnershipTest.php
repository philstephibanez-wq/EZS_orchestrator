<?php
declare(strict_types=1);
require_once dirname(__DIR__).'/src/Module/Infrastructure/DevBackendOwnership.php';
$state=(new \Ezs\Web\Module\Infrastructure\DevBackendOwnership())->snapshot();
if ($state['port']!==8602 || !in_array($state['ownership'],['absent','unknown','unverified'],true)) throw new RuntimeException('ownership_misreported');
if ($state['ownership']==='absent' && $state['tcp_listening']) throw new RuntimeException('invalid_absent');
echo "DEV_BACKEND_OWNERSHIP_OK\n";
