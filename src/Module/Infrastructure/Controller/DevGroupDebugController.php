<?php

declare(strict_types=1);

namespace Ezs\Web\Module\Infrastructure\Controller;

use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

/** Diagnostic DEV non mutateur, sans affichage de secrets ou d'identifiants de session. */
final class DevGroupDebugController
{
    public static function allowed(string $environment, string $host, string $ip): bool
    {
        return $environment === 'dev'
            && in_array($host, ['127.0.0.1', 'localhost'], true)
            && in_array($ip, ['127.0.0.1', '::1'], true);
    }

    /** Expose uniquement les catégories d'état, jamais les PID, commandes ou jetons. */
    public static function summary(array $states): array
    {
        $result = [];
        foreach (NativeWindowsLifecycle::groups() as $group => $names) {
            $members = [];
            foreach ($names as $name) {
                $members[$name] = (string) ($states[$name] ?? 'MISSING');
            }
            $result[$group] = $members;
        }
        return $result;
    }

    #[Route('/api/v2/infrastructure/dev-debug-native', name: 'ezs_dev_group_debug_native', methods: ['GET'])]
    public function native(Request $request): Response
    {
        if (!self::allowed(
            (string) ($_SERVER['APP_ENV'] ?? getenv('APP_ENV') ?: ''),
            $request->getHost(),
            (string) $request->getClientIp()
        )) {
            return new Response('forbidden', 403, ['Cache-Control' => 'no-store']);
        }
        try {
            $result = [
                'schema' => 'ezs.dev_group_native_debug.v1',
                'groups' => self::summary((new NativeWindowsLifecycle())->status()),
                'error' => null,
            ];
        } catch (\Throwable $failure) {
            $result = [
                'schema' => 'ezs.dev_group_native_debug.v1',
                'groups' => [],
                'error' => 'INVENTORY_UNAVAILABLE',
            ];
        }
        return new Response(json_encode($result, JSON_THROW_ON_ERROR), 200, [
            'Content-Type' => 'application/json; charset=UTF-8',
            'Cache-Control' => 'no-store',
            'X-Content-Type-Options' => 'nosniff',
            'X-Robots-Tag' => 'noindex, nofollow',
        ]);
    }
}
