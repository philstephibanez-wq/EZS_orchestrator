<?php

declare(strict_types=1);

require_once dirname(__DIR__).'/src/Module/Infrastructure/EnvironmentCatalog.php';

use Ezs\Web\Module\Infrastructure\EnvironmentCatalog;

$rows = (new EnvironmentCatalog())->all();
if (count($rows) !== 5) { throw new RuntimeException('environment_count'); }
foreach ($rows as $row) {
    if ($row['environment'] === 'prod' && $row['component'] !== 'ezstudio') { throw new RuntimeException('forbidden_production'); }
    if ($row['maintenance'] && ($row['component'] !== 'ezstudio' || $row['environment'] !== 'prod')) { throw new RuntimeException('forbidden_maintenance'); }
}
echo "ENVIRONMENT_CATALOG_OK\n";
