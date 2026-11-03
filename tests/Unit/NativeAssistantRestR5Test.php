<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
use Ezs\Web\Module\Infrastructure\NativeSiteObservation;
use Ezs\Web\Module\Infrastructure\NativeSiteLifecycle;
final class NativeAssistantRestR5Test extends TestCase
{
    public function testAssistantColdHotAndForeignObservation(): void
    {
        $cold=NativeSiteObservation::classify('assistant','SITE=assistant INTENT=STOPPED OWNED=0 LISTENERS=0');
        self::assertSame('STOPPED',$cold['state']);
        self::assertTrue($cold['start']);
        $hot=NativeSiteObservation::classify('assistant','SITE=assistant INTENT=RUNNING OWNED=1 LISTENERS=3');
        self::assertSame('RUNNING',$hot['state']);
        self::assertTrue($hot['stop']);
        foreach(['SITE=assistant INTENT=RUNNING OWNED=2 LISTENERS=3',
                 'SITE=assistant INTENT=RUNNING OWNED=0 LISTENERS=3'] as $bad) {
            $state=NativeSiteObservation::classify('assistant',$bad);
            self::assertSame('UNVERIFIED',$state['state']);
            self::assertFalse($state['start']);
            self::assertFalse($state['stop']);
        }
    }
    public function testAssistantActionsUseCanonicalSiteBridge(): void
    {
        $args=NativeSiteLifecycle::arguments('assistant','Start');
        self::assertSame('assistant',$args[array_search('-Site',$args,true)+1]);
        $src=(string)file_get_contents(dirname(__DIR__,2).'/scripts/ezs_assistant_stack.ps1');
        self::assertStringContainsString('scripts\\start.ps1',$src);
        self::assertStringContainsString('scripts\\stop.ps1',$src);
        self::assertStringNotContainsString('Start-Process -FilePath $franken',$src);
    }
}
