<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeSiteLifecycle;

final class DevAppsRecovery024Test extends TestCase
{
    public function testNativeSitePlanIsPureAndDoesNotStartAnyService(): void
    {
        foreach (['dev','lab','assistant'] as $site) {
            $args = NativeSiteLifecycle::arguments($site, 'Preflight');
            self::assertSame($site,$args[array_search('-Site',$args,true)+1]);
            self::assertSame('Preflight',end($args));
        }
    }
}
