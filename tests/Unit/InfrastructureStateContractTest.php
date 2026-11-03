<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class InfrastructureStateContractTest extends TestCase
{
    public function testWebHardBadgeDoesNotClaimBusinessHealth(): void
    {
        $root=dirname(__DIR__,2);
        $js=(string)file_get_contents($root.'/public/assets/ezs-web-hard.js');
        self::assertStringContainsString('/api/v2/infrastructure/web-hard-ping',$js);
        self::assertStringNotContainsString('/dev-groups/',$js);
        self::assertStringNotContainsString('Start-Process',$js);
        self::assertStringNotContainsString('Stop-Process',$js);
    }
    public function testWebPageAndTechnicalStatusRemainSeparate(): void
    {
        $root=dirname(__DIR__,2);
        $twig=(string)file_get_contents($root.'/templates/infrastructure/index.html.twig');
        self::assertStringContainsString('id="state-dev"',$twig);
        self::assertStringContainsString('id="state-lab"',$twig);
        self::assertStringContainsString('id="state-assistant"',$twig);
        self::assertStringContainsString('href="http://127.0.0.1:8502/fr/catalog"',$twig);
        self::assertStringContainsString('href="http://127.0.0.1:8702/"',$twig);
        self::assertStringContainsString('href="http://127.0.0.1:8712/"',$twig);
    }
    public function testAssetCacheIsVersioned(): void
    {
        $twig=(string)file_get_contents(dirname(__DIR__,2).'/templates/infrastructure/index.html.twig');
        self::assertStringContainsString('ezs-web-hard.js?v={{ orchestrator_version|url_encode }}',$twig);
        self::assertStringContainsString('ezs-prod-control.js?v={{ orchestrator_version|url_encode }}',$twig);
    }
}
