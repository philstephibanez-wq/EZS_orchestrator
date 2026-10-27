<?php
declare(strict_types=1);

namespace Ezs\Web\Module\Infrastructure\Controller;

use Ezs\Web\Module\Infrastructure\LocalPortStatus;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

/**
 * Read-only compatibility boundary. Never returns invented job/process state.
 * Historic state-changing endpoints intentionally do not exist in V2.
 */
final class LegacyReadOnlyController
{
    #[Route('/api/status', name: 'ezs_v2_compat_status', methods: ['GET'])]
    public function status(Request $request, LocalPortStatus $ports): JsonResponse
    {
        if (!$this->loopback($request)) {
            return new JsonResponse(['ok' => false, 'error' => 'forbidden'], 403);
        }

        return new JsonResponse([
            'ok' => true,
            'schema' => 'ezs.orchestrator.v2.readonly.v1',
            'migration' => 'in_progress',
            'source' => 'symfony_root',
            'capabilities' => ['infrastructure_tcp' => true, 'jobs' => false, 'actions' => false],
            'listeners' => $ports->snapshot(),
        ], 200, ['Cache-Control' => 'no-store']);
    }

    #[Route('/api/jobs', name: 'ezs_v2_compat_jobs', methods: ['GET'])]
    public function jobs(Request $request): JsonResponse
    {
        if (!$this->loopback($request)) {
            return new JsonResponse(['ok' => false, 'error' => 'forbidden'], 403);
        }
        return new JsonResponse([
            'ok' => false,
            'error' => 'jobs_migration_pending',
            'jobs' => [],
            'note' => 'Aucun job n’est interrogé ou exécuté par cette route.',
        ], 503, ['Cache-Control' => 'no-store']);
    }

    private function loopback(Request $request): bool
    {
        return in_array($request->getHost(), ['127.0.0.1', 'localhost'], true)
            && in_array($request->getClientIp(), ['127.0.0.1', '::1'], true);
    }
}
