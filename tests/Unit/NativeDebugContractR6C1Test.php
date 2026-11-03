<?php
declare(strict_types=1);

use PHPUnit\Framework\TestCase;

final class NativeDebugContractR6C1Test extends TestCase
{
    public function testHistoricalFailureMarkerAndReadOnlyDiagnosticsRemain(): void
    {
        $root=dirname(__DIR__,2);
        $code=(string)file_get_contents($root.'/src/Module/Infrastructure/Controller/DevGroupDebugController.php');
        self::assertStringContainsString('INVENTORY_UNAVAILABLE',$code);
        self::assertStringContainsString("'diagnostics'=>\$diagnostics",$code);
        self::assertStringContainsString("'timestamp_utc'=>gmdate",$code);
        self::assertStringContainsString("'error'=>\$failed === count(\$diagnostics)",$code);
        self::assertStringNotContainsString('NativeWindowsLifecycle',$code);
        self::assertStringNotContainsString('Stop-Process',$code);
    }
}
