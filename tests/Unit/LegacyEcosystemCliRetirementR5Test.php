<?php
declare(strict_types=1);

use Ezs\Web\Module\Infrastructure\NativeSiteLifecycle;
use PHPUnit\Framework\TestCase;

/** Removal contract: old bulk commands may no longer start PHP-CGI or Assistant implicitly. */
final class LegacyEcosystemCliRetirementR5Test extends TestCase
{
    public function testBothLegacyBulkCommandEntryPointsArePhysicallyRemoved(): void
    {
        $root = dirname(__DIR__, 2);
        self::assertFileDoesNotExist($root.'/src/Module/Infrastructure/EcosystemEntryCommand.php');
        self::assertFileDoesNotExist($root.'/src/Module/Infrastructure/EcosystemStopCommand.php');
    }

    public function testSupportedReplacementDelegatesDevLabAndAssistant(): void
    {
        foreach (['dev','lab','assistant'] as $site) {
            foreach (['Preflight','Status','Start','Stop'] as $action) {
                $args = NativeSiteLifecycle::arguments($site, $action);
                self::assertSame($site, $args[array_search('-Site', $args, true) + 1]);
                self::assertSame($action, $args[array_search('-Action', $args, true) + 1]);
            }
        }
        $this->expectException(\RuntimeException::class);
        NativeSiteLifecycle::arguments('prod', 'Stop');
    }

    public function testCurrentSupervisorDoesNotCallTheLegacyWindowsEngine(): void
    {
        $code = (string) file_get_contents(dirname(__DIR__, 2).
            '/src/Module/Infrastructure/ServiceSupervisorCommand.php');
        self::assertStringContainsString('NativeSiteLifecycle', $code);
        self::assertStringNotContainsString('NativeWindowsLifecycle', $code);
        self::assertStringNotContainsString('reconcileFastCgiGroup', $code);
    }
}
