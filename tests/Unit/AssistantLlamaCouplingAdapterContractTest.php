<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class AssistantLlamaCouplingAdapterContractTest extends TestCase {
    public function testAssistantOwnsLlamaLifecycleWithoutPersistedIntent(): void {
        $s=(string)file_get_contents(dirname(__DIR__,2).'/scripts/ezs_assistant_stack.ps1');
        self::assertStringContainsString('scripts\\start.ps1',$s);
        self::assertStringContainsString('scripts\\stop.ps1',$s);
        self::assertStringContainsString('ASSISTANT_CANONICAL_', $s);
        self::assertStringContainsString('ASSISTANT_SAFE_STOP_REFUSED',$s);
        self::assertStringNotContainsString('desired-services.json',$s);
        self::assertStringNotContainsString('Read-Desired',$s);
        self::assertStringContainsString('& powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $entry',$s);
        self::assertStringNotContainsString('Start-Process',$s);
        self::assertStringNotContainsString('Stop-Process',$s);
    }
}
