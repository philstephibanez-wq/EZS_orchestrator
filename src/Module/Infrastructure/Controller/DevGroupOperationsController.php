<?php
declare(strict_types=1);

namespace Ezs\Web\Module\Infrastructure\Controller;

use Ezs\Web\Module\Infrastructure\NativeWindowsLifecycle;
use Ezs\Web\Module\Infrastructure\DesiredServiceState;
use Ezs\Web\Module\Infrastructure\SymfonyDevCachePreparation;
use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

/** Local control only. Existing NativeWindowsLifecycle remains the sole lifecycle authority. */
final class DevGroupOperationsController
{
    public static function allowed(string $environment, string $host, string $ip): bool
    {
        return $environment === 'dev'
            && in_array($host, ['127.0.0.1', 'localhost'], true)
            && in_array($ip, ['127.0.0.1', '::1'], true);
    }

    public static function permission(array $states, string $group): array
    {
        $groups = NativeWindowsLifecycle::groups();
        if (!isset($groups[$group])) throw new \InvalidArgumentException('EZS_DEV_GROUP_UNKNOWN');
        $names = $groups[$group];
        foreach (NativeWindowsLifecycle::specs() as $name => $_spec) {
            if (!array_key_exists($name, $states) || !in_array($states[$name], ['ATTESTED', 'ABSENT'], true)) {
                return ['start' => false, 'restart' => false, 'stop' => false, 'state' => 'UNVERIFIED'];
            }
        }
        $values = array_map(static fn(string $name): string => $states[$name], $names);
        $allUp = count(array_filter($values, static fn(string $s): bool => $s === 'ATTESTED')) === count($values);
        $allDown = count(array_filter($values, static fn(string $s): bool => $s === 'ABSENT')) === count($values);
        return [
            // DEV and Preview share one Symfony cache: refuse partial cold start while sibling runs.
            'start' => $allDown,
            'restart' => $allUp,
            'stop' => !$allDown,
            'state' => $allUp ? 'RUNNING' : ($allDown ? 'STOPPED' : 'PARTIAL'),
        ];
    }

    private function allowedRequest(Request $request): bool
    {
        return self::allowed(
            (string) ($_SERVER['APP_ENV'] ?? getenv('APP_ENV') ?: ''),
            $request->getHost(),
            (string) $request->getClientIp()
        );
    }

    private function token(): string
    {
        if (session_status() !== PHP_SESSION_ACTIVE) {
            session_start(['cookie_httponly' => true, 'cookie_samesite' => 'Strict', 'use_strict_mode' => true]);
        }
        if (!isset($_SESSION['ezs_dev_group_csrf'])) {
            $_SESSION['ezs_dev_group_csrf'] = bin2hex(random_bytes(32));
        }
        return (string) $_SESSION['ezs_dev_group_csrf'];
    }

    #[Route('/api/v2/infrastructure/dev-groups', name: 'ezs_dev_groups_read', methods: ['GET'])]
    public function read(Request $request): JsonResponse
    {
        if (!$this->allowedRequest($request)) return new JsonResponse(['error' => 'forbidden'], 403);
        $token = $this->token();
        try {
            $lifecycle = new NativeWindowsLifecycle();
            $states = $lifecycle->status();
            $groups = [];
            foreach (NativeWindowsLifecycle::groups() as $name => $_members) {
                $groups[$name] = self::permission($states, $name);
            }
            return new JsonResponse([
                'schema' => 'ezs.dev_groups.v1',
                'csrf' => $token,
                'groups' => $groups,
            ], 200, ['Cache-Control' => 'no-store']);
        } catch (\Throwable $failure) {
            return new JsonResponse(['error' => $failure->getMessage()], 503, ['Cache-Control' => 'no-store']);
        }
    }

    #[Route('/api/v2/infrastructure/dev-groups/{group}/{action}', name: 'ezs_dev_groups_action', requirements: ['group' => 'dev|lab|assistant', 'action' => 'start|stop|restart'], methods: ['POST'])]
    public function action(Request $request, string $group, string $action): JsonResponse
    {
        if (!$this->allowedRequest($request)) return new JsonResponse(['error' => 'forbidden'], 403);
        if (!in_array($request->headers->get('Origin', ''), ['http://127.0.0.1:8790', 'http://localhost:8790'], true)) {
            return new JsonResponse(['error' => 'invalid_origin'], 403);
        }
        if (!hash_equals($this->token(), (string) $request->headers->get('X-EZS-CSRF', ''))) {
            return new JsonResponse(['error' => 'csrf'], 403);
        }
        if ((string) $request->request->get('confirmation', '') !== strtoupper($action).'_'.strtoupper($group)) {
            return new JsonResponse(['error' => 'confirmation_required'], 400);
        }
        try {
            $lifecycle = new NativeWindowsLifecycle();
            $states = $lifecycle->status();
            $permission = self::permission($states, $group);
            if (!$permission[$action]) {
                return new JsonResponse(['error' => 'action_not_available'], 409, ['Cache-Control' => 'no-store']);
            }
            // L'intention est durable AVANT toute mutation de processus.
            (new DesiredServiceState())->set($group, $action === 'stop' ? DesiredServiceState::STOPPED : DesiredServiceState::RUNNING);
            if ($action === 'start') {
                $specs = array_intersect_key(NativeWindowsLifecycle::specs(), array_flip(NativeWindowsLifecycle::groups()[$group]));
                $roots = SymfonyDevCachePreparation::rootsToPrepare(array_intersect_key($states, $specs), $specs);
                SymfonyDevCachePreparation::prepare($roots);
                $result = $lifecycle->startGroup($group);
            } elseif ($action === 'restart') {
                // Le cycle natif refuse tout PID non attesté et contrôle son identité à chaque arrêt.
                // Vérifier les dépendances de relance AVANT toute interruption.
                $specs = array_intersect_key(NativeWindowsLifecycle::specs(), array_flip(NativeWindowsLifecycle::groups()[$group]));
                foreach ($specs as $name => $spec) {
                    if (!is_file($spec['exe']) || !is_dir($spec['cwd'])) {
                        return new JsonResponse(['error' => 'restart_dependency_unavailable_'.$name], 409, ['Cache-Control' => 'no-store']);
                    }
                }
                $stopped = $lifecycle->stopGroup($group);
                try {
                    $afterStop = $lifecycle->status();
                    if (self::permission($afterStop, $group)['state'] !== 'STOPPED') {
                        throw new \RuntimeException('EZS_RESTART_STOP_NOT_VERIFIED');
                    }
                    $roots = SymfonyDevCachePreparation::rootsToPrepare(array_intersect_key($afterStop, $specs), $specs);
                    SymfonyDevCachePreparation::prepare($roots);
                    $started = $lifecycle->startGroup($group);
                    $afterStart = $lifecycle->status();
                    if (self::permission($afterStart, $group)['state'] !== 'RUNNING') {
                        throw new \RuntimeException('EZS_RESTART_START_NOT_VERIFIED');
                    }
                    $result = ['stopped' => $stopped, 'started' => $started];
                } catch (\Throwable $restartFailure) {
                    // Ne jamais tenter de récupération implicite sur une identité incertaine.
                    return new JsonResponse(['error' => 'restart_incomplete', 'phase' => 'after_stop'], 503, ['Cache-Control' => 'no-store']);
                }
            } else {
                $result = $lifecycle->stopGroup($group);
            }
            return new JsonResponse([
                'schema' => 'ezs.dev_group_action.v1',
                'group' => $group,
                'action' => $action,
                'processes' => $result,
            ], 200, ['Cache-Control' => 'no-store']);
        } catch (\Throwable $failure) {
            return new JsonResponse(['error' => $failure->getMessage()], 503, ['Cache-Control' => 'no-store']);
        }
    }
}
