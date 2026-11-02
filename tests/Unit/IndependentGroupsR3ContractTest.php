<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class IndependentGroupsR3ContractTest extends TestCase
{
    public function testPerGroupReadAndActionDoNotDisableOthers(): void
    {
        $root=dirname(__DIR__,2);
        $js=(string)file_get_contents($root.'/public/assets/ezs-infrastructure.js');
        $php=(string)file_get_contents($root.'/src/Module/Infrastructure/Controller/DevGroupOperationsController.php');
        self::assertStringContainsString("'/api/v2/infrastructure/dev-group/'+group", $js);
        self::assertStringContainsString('function refreshGroup(group)', $js);
        self::assertStringContainsString('groupActing[group] = true', $js);
        self::assertStringContainsString('groupActing[group] = false', $js);
        self::assertStringContainsString('refreshGroup(group);', $js);
        self::assertStringNotContainsString('acting = true;', $js);
        self::assertStringNotContainsString('acting = false;', $js);
        self::assertStringContainsString('ezs.dev_group_single.v1', $php);
        self::assertStringContainsString("methods: ['GET']", $php);
    }
}
