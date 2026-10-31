<?php
declare(strict_types=1);
require_once dirname(__DIR__,2).'/src/Module/Infrastructure/FastCgiProcessClassification.php';
use Ezs\Web\Module\Infrastructure\FastCgiProcessClassification as C;
if (C::label(true,true)!=='ACTIVE') throw new RuntimeException('ACTIVE');
if (C::label(true,false)!=='RESIDUAL') throw new RuntimeException('RESIDUAL');
if (C::label(false,true)!=='UNVERIFIED') throw new RuntimeException('FOREIGN');
if (C::label(false,false)!=='UNVERIFIED') throw new RuntimeException('UNKNOWN');
echo "EZS_FASTCGI_CLASSIFICATION_067_OK\n";
