<?php
declare(strict_types=1);
require_once __DIR__.'/../src/Module/Infrastructure/WindowsPortOwnership.php';
use Ezs\Web\Module\Infrastructure\WindowsPortOwnership as P;
$lines="  TCP    127.0.0.1:8790    0.0.0.0:0    LISTENING    16448\r\n  TCP    127.0.0.1:8791    0.0.0.0:0    LISTENING    23780\r\n";
$p=P::parseListeners($lines);
if($p[8790]!==[16448]||$p[8791]!==[23780])throw new RuntimeException('NETSTAT_PARSE_FAILED');
$t=P::parseTasks("\"php-cgi.exe\",\"23780\",\"Console\"\r\n");
if(($t[23780]??null)!=='php-cgi.exe')throw new RuntimeException('TASKLIST_PARSE_FAILED');
$cli=file_get_contents(__DIR__.'/../bin/infrastructure.php');
if(!str_contains($cli,'WindowsPortOwnership::snapshot'))throw new RuntimeException('PHP_OWNERSHIP_NOT_WIRED');
echo "EZS_PHP_PID_DIAGNOSTIC_CONTRACT_OK\n";
