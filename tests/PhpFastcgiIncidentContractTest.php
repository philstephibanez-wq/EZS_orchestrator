<?php
declare(strict_types=1);
require_once __DIR__.'/../src/Module/Infrastructure/FastcgiIncidentReport.php';
use Ezs\Web\Module\Infrastructure\FastcgiIncidentReport;
$report=FastcgiIncidentReport::collect(dirname(__DIR__),['php_pid'=>123]);
if($report['expected_pid']!==123||$report['port']!==8791||$report['diagnostic_only']!==true)throw new RuntimeException('FASTCGI_INCIDENT_REPORT_INVALID');
$cli=(string)file_get_contents(__DIR__.'/../bin/infrastructure.php');
if(!str_contains($cli,"'fastcgi-incident'"))throw new RuntimeException('FASTCGI_INCIDENT_COMMAND_MISSING');
echo "EZS_PHP_FASTCGI_INCIDENT_CONTRACT_OK\n";
