<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Infrastructure;

/** Contrôles conservateurs pour un arrêt déjà effectif ou un état sans processus. */
final class EcosystemLifecycleGuard
{
    public const STATES = [
        'runtime/v2-dev/processes.json' => ['php_pid', 'caddy_pid'],
        'runtime/v2-dev/app-backends.json' => ['dev_pid', 'preview_pid'],
        'runtime/v2-dev/lab-assistant.json' => ['lab_pid', 'assistant_pid'],
        'runtime/v2-dev/assistant-ai.json' => ['pid'],
        'runtime/v2-prod/processes.json' => ['php_pid', 'internal_pid', 'gateway_pid', 'edge_pid'],
    ];
    public const PORTS = [8790,8791,8502,8852,8602,8862,8701,8702,8712,8713,8720,8501,8510,8511,8512];
    public const PROD_PORTS = [8501,8510,8511,8512];

    /** @param array<string,array<string,mixed>> $states @param list<int> $livePids @param list<int> $openPorts */
    public static function canClean(array $states, array $livePids, array $openPorts): bool
    {
        if ($openPorts !== [] || $livePids !== []) return false;
        foreach ($states as $name => $state) {
            if (!isset(self::STATES[$name]) || !is_array($state)) return false;
            foreach (self::STATES[$name] as $key) {
                if (isset($state[$key]) && (!is_numeric($state[$key]) || (int)$state[$key] < 0)) return false;
            }
        }
        return true;
    }

    /** @param list<int> $livePids @param list<int> $openPorts */
    public static function prodFullyStopped(array $livePids, array $openPorts): bool
    {
        return $livePids === [] && array_intersect(self::PROD_PORTS, $openPorts) === [];
    }
}
