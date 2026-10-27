<?php
declare(strict_types=1);
require_once dirname(__DIR__).'/src/Module/Infrastructure/ProdFastcgiPreflight.php';

use Ezs\Web\Module\Infrastructure\ProdFastcgiPreflight;

$method = new ReflectionMethod(ProdFastcgiPreflight::class, 'inspect');
if (!$method->isPublic() || !$method->isStatic()) throw new RuntimeException('PREFLIGHT_INTERFACE_INVALID');
$source = file_get_contents(dirname(__DIR__).'/src/Module/Infrastructure/ProdFastcgiPreflight.php');
foreach (['php_fastcgi 127.0.0.1:8512','PROD_ROOT_UNEXPECTED','PROD_DEV_ROOT_COLLISION','candidate_only'] as $required) {
    if (!str_contains($source, $required)) throw new RuntimeException('MISSING_GUARD:'.$required);
}
foreach (['proc_open(', 'shell_exec(', 'exec(', 'passthru(', 'unlink(', 'rename('] as $forbidden) {
    if (str_contains($source, $forbidden)) throw new RuntimeException('NOT_READ_ONLY:'.$forbidden);
}
echo "PROD_FASTCGI_PHP_CANDIDATE_CONTRACT_OK\n";
