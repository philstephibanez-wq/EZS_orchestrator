<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Infrastructure;

/** Bounded, non-mutating interpretation of the canonical FrankenPHP Status output.
 * RUNNING is an observation only; the PowerShell lifecycle reattests ownership
 * before any destructive action. Never expose PIDs, commands, or environment.
 */
final class NativeSiteObservation
{
    private const PORTS = ['dev' => 2, 'lab' => 2];

    public function __construct(private readonly NativeSiteLifecycle $lifecycle = new NativeSiteLifecycle()) {}

    public static function classify(string $site, string $text): array
    {
        if (!isset(self::PORTS[$site])) throw new \InvalidArgumentException('EZS_NATIVE_OBSERVATION_SITE_REFUSED');
        $lines = preg_split('/\r?\n/', $text) ?: [];
        $evidence = [];
        foreach ($lines as $line) {
            if (!str_starts_with($line, 'SITE=')) continue;
            if (count($evidence) !== 0 || !preg_match('/^SITE=(dev|lab) INTENT=(RUNNING|STOPPED) OWNED=(\d+) LISTENERS=(\d+)$/D', $line, $matches)) {
                throw new \RuntimeException('EZS_NATIVE_OBSERVATION_UNVERIFIED');
            }
            $evidence = $matches;
        }
        if ($evidence === [] || $evidence[1] !== $site) throw new \RuntimeException('EZS_NATIVE_OBSERVATION_MISSING');
        $owned = (int) $evidence[3]; $listeners = (int) $evidence[4];
        $state = $owned === 0 && $listeners === 0 ? 'STOPPED'
            : ($owned === 1 && $listeners === self::PORTS[$site] ? 'RUNNING' : 'UNVERIFIED');
        return [
            'state' => $state,
            'start' => $state === 'STOPPED',
            'stop' => $state === 'RUNNING',
            'restart' => $state === 'RUNNING',
            'desired' => $evidence[2],
        ];
    }

    public function observe(string $site): array
    {
        return self::classify($site, $this->lifecycle->request($site, 'Status'));
    }
}
