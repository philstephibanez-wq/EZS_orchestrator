<?php

declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class InfrastructureStateTriadContractTest extends TestCase
{
    public function testBadgesClassifyUsingDesiredAndNativeState(): void
    {
        $js = (string) file_get_contents(dirname(__DIR__, 2) . '/public/assets/ezs-infrastructure.js');
        self::assertStringContainsString("native === 'STOPPED' && desired === 'STOPPED'", $js);
        self::assertStringContainsString("native === 'RUNNING' && desired === 'RUNNING'", $js);
        self::assertStringContainsString("'ONLINE'", $js);
        self::assertStringContainsString("'OFFLINE'", $js);
        self::assertStringContainsString("'ERREUR'", $js);
        self::assertStringContainsString(".attr('aria-disabled', online ? 'false' : 'true')", $js);
        self::assertStringContainsString("if ($(this).attr('aria-disabled') === 'true') event.preventDefault();", $js);
    }
    public function testGetGroupsReportsDesiredSeparately(): void
    {
        $php = (string) file_get_contents(dirname(__DIR__, 2) . '/src/Module/Infrastructure/Controller/DevGroupOperationsController.php');
        self::assertStringContainsString('$groups[$name][\'desired\'] = (new DesiredServiceState())->get($name);', $php);
    }
}
