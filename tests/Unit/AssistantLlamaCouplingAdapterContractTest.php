<?php
declare(strict_types=1);
use PHPUnit\Framework\TestCase;
final class AssistantLlamaCouplingAdapterContractTest extends TestCase {
    public function testAssistantOwnsLlamaLifecycle(): void {
        $s=file_get_contents(dirname(__DIR__,2).'/scripts/ezs_assistant_stack.ps1');
        self::assertIsString($s);
        self::assertStringContainsString('scripts\\start.ps1',$s);
        self::assertStringContainsString('scripts\\stop.ps1',$s);
        self::assertStringContainsString('ASSISTANT_START_REFUSED_DESIRED_STOPPED',$s);
        self::assertStringContainsString('ASSISTANT_STOP_REFUSED_DESIRED_RUNNING',$s);
        self::assertStringContainsString('ASSISTANT_INTENT_CHANGED',$s);
        self::assertStringContainsString('& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $entry',$s);
        self::assertStringNotContainsString('Start-Process',$s);
        self::assertStringNotContainsString('Stop-Process',$s);
        self::assertStringNotContainsString('php-cgi.exe',$s);
    }
}
