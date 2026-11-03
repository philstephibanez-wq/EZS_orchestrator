<?php

declare(strict_types=1);

namespace Ezs\Web\Module\Infrastructure\Controller;

use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

/** DEV maintenance is a route-only switch, never a process lifecycle operation. */
final class DevWebModeController
{
    private const FLAG_DIR = 'H:/EZS_orchestrator/runtime/web-modes';
    private const FLAG = self::FLAG_DIR.'/dev.maintenance';

    public static function allowed(string $environment, string $host, string $ip): bool
    {
        return $environment === 'dev'
            && in_array($host, ['127.0.0.1', 'localhost'], true)
            && in_array($ip, ['127.0.0.1', '::1'], true);
    }

    private static function token(): string
    {
        if (session_status() !== PHP_SESSION_ACTIVE) {
            session_start(['cookie_httponly' => true, 'cookie_samesite' => 'Strict', 'use_strict_mode' => true]);
        }
        if (!isset($_SESSION['ezs_dev_web_mode_csrf'])) {
            $_SESSION['ezs_dev_web_mode_csrf'] = bin2hex(random_bytes(32));
        }
        return (string) $_SESSION['ezs_dev_web_mode_csrf'];
    }

    private static function permitted(Request $request): bool
    {
        return self::allowed((string) ($_SERVER['APP_ENV'] ?? getenv('APP_ENV') ?: ''),
            $request->getHost(), (string) $request->getClientIp());
    }

    #[Route('/api/v2/infrastructure/dev-web-mode', name: 'ezs_dev_web_mode_read', methods: ['GET'])]
    public function read(Request $request): JsonResponse
    {
        if (!self::permitted($request)) return new JsonResponse(['error'=>'forbidden'],403);
        return new JsonResponse([
            'schema'=>'ezs.dev_web_mode.v1',
            'mode'=>is_file(self::FLAG) ? 'MAINTENANCE' : 'NORMAL',
            'csrf'=>self::token(),
        ],200,['Cache-Control'=>'no-store']);
    }

    #[Route('/api/v2/infrastructure/dev-web-mode/{mode}', name: 'ezs_dev_web_mode_change', requirements: ['mode'=>'normal|maintenance'], methods: ['POST'])]
    public function change(Request $request, string $mode): JsonResponse
    {
        if (!self::permitted($request)) return new JsonResponse(['error'=>'forbidden'],403);
        if (!in_array($request->headers->get('Origin', ''),
            ['http://127.0.0.1:8790','http://localhost:8790'], true)) {
            return new JsonResponse(['error'=>'invalid_origin'],403);
        }
        if (!hash_equals(self::token(), (string) $request->headers->get('X-EZS-CSRF',''))) {
            return new JsonResponse(['error'=>'csrf'],403);
        }
        if ((string) $request->request->get('confirmation','') !== strtoupper($mode).'_DEV') {
            return new JsonResponse(['error'=>'confirmation_required'],400);
        }
        if (!is_dir(self::FLAG_DIR) && !@mkdir(self::FLAG_DIR,0750,true) && !is_dir(self::FLAG_DIR)) {
            return new JsonResponse(['error'=>'dev_mode_dir_unavailable'],503);
        }
        $lock=@fopen(self::FLAG_DIR.'/dev-mode.lock','c+');
        if (!is_resource($lock)) return new JsonResponse(['error'=>'dev_mode_lock_unavailable'],503);
        try {
            if (!flock($lock,LOCK_EX|LOCK_NB)) return new JsonResponse(['error'=>'dev_mode_busy'],409);
            if ($mode === 'maintenance') {
                if (!is_file(self::FLAG) && file_put_contents(self::FLAG,"MAINTENANCE\n",LOCK_EX) === false) {
                    return new JsonResponse(['error'=>'dev_mode_write_failed'],503);
                }
            } elseif (is_file(self::FLAG) && !@unlink(self::FLAG)) {
                return new JsonResponse(['error'=>'dev_mode_remove_failed'],503);
            }
            $observed=is_file(self::FLAG) ? 'MAINTENANCE' : 'NORMAL';
            if ($observed !== strtoupper($mode)) return new JsonResponse(['error'=>'dev_mode_not_confirmed'],503);
            return new JsonResponse(['schema'=>'ezs.dev_web_mode.v1','mode'=>$observed],200,['Cache-Control'=>'no-store']);
        } finally {
            flock($lock,LOCK_UN);
            fclose($lock);
        }
    }
}
