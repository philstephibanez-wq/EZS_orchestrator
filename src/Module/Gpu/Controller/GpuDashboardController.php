<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Gpu\Controller;

use Ezs\Web\Module\Gpu\GpuProbe;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

final class GpuDashboardController
{
    #[Route('/api/v2/gpu/dashboard', name: 'ezs_v2_gpu_dashboard', methods: ['GET'])]
    public function dashboard(Request $request, GpuProbe $probe): JsonResponse
    {
        // This endpoint is strictly for the loopback-only DEV preflight,
        // not a production substitute for authenticated machine telemetry.
        $host = $request->getHost();
        if (($_SERVER['APP_ENV'] ?? getenv('APP_ENV') ?: '') !== 'dev'
            || !in_array($host, ['127.0.0.1', 'localhost'], true)
            || !in_array($request->getClientIp(), ['127.0.0.1', '::1'], true)) {
            return new JsonResponse(['available' => false, 'error' => 'forbidden'], 403);
        }
        try {
            $result = $probe->read();
            return new JsonResponse([
                'available' => true,
                'timestamp_ms' => (int)round(microtime(true) * 1000),
                'gpu' => $result['gpu'],
            ], 200, ['Cache-Control' => 'no-store']);
        } catch (\Throwable) {
            return new JsonResponse(['available' => false, 'error' => 'gpu_unavailable'], 503);
        }
    }
}
