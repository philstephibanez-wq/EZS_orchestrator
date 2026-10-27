<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Infrastructure\Controller;

use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;
use Symfony\Component\Process\Process;

final class ProdOperationsController
{
    private function allowed(Request $request): bool
    {
        return ($_SERVER['APP_ENV'] ?? getenv('APP_ENV') ?: '') === 'dev'
            && in_array($request->getHost(), ['127.0.0.1', 'localhost'], true)
            && in_array($request->getClientIp(), ['127.0.0.1', '::1'], true);
    }

    private function sessionToken(): string
    {
        if (session_status() !== PHP_SESSION_ACTIVE) {
            session_start(['cookie_httponly'=>true,'cookie_samesite'=>'Strict','use_strict_mode'=>true]);
        }
        if (!isset($_SESSION['ezs_prod_csrf'])) {
            $_SESSION['ezs_prod_csrf'] = bin2hex(random_bytes(32));
        }
        return (string) $_SESSION['ezs_prod_csrf'];
    }

    #[Route('/api/v2/infrastructure/prod-control', name:'ezs_prod_control_read', methods:['GET'])]
    public function read(Request $request): JsonResponse
    {
        if (!$this->allowed($request)) return new JsonResponse(['error'=>'forbidden'],403);
        $token = $this->sessionToken();
        $root = dirname(__DIR__, 4);
        $config = 'H:/EZScore/var/runtime/online-gateway.json';
        $desired = null;
        if (is_file($config)) {
            $data = json_decode((string) file_get_contents($config), true);
            if (is_array($data) && is_bool($data['maintenance'] ?? null)) $desired = $data['maintenance'];
        }
        $gateway = null;
        $context = stream_context_create(['http'=>['timeout'=>1,'ignore_errors'=>true]]);
        $raw = @file_get_contents('http://127.0.0.1:8510/__ezscore_gateway_status',false,$context);
        if (is_string($raw)) {
            $data = json_decode($raw,true);
            if (is_array($data) && ($data['protocol'] ?? '') === 'ezscore.online-gateway.v3' && ($data['ok'] ?? false) === true) $gateway=$data;
        }
        $socket=@stream_socket_client('tcp://127.0.0.1:8501',$errno,$errstr,0.5);
        $caddy=is_resource($socket);
        if ($caddy) fclose($socket);
        return new JsonResponse([
            'schema'=>'ezs.prod_control.v1',
            'gateway_online'=>$gateway!==null,
            'caddy_listening'=>$caddy,
            'maintenance'=>$gateway['maintenance'] ?? null,
            'desired_maintenance'=>$desired,
            'csrf'=>$token,
            'actions'=>['maintenance'=>$gateway!==null && $caddy, 'normal'=>false],
            'note'=>'La sortie de maintenance est bloquée jusqu’à migration FastCGI et autorisation opérateur.',
        ],200,['Cache-Control'=>'no-store']);
    }

    #[Route('/api/v2/infrastructure/prod-control/maintenance', name:'ezs_prod_control_maintenance', methods:['POST'])]
    public function maintenance(Request $request): JsonResponse
    {
        if (!$this->allowed($request)) return new JsonResponse(['error'=>'forbidden'],403);
        $origin=$request->headers->get('Origin','');
        if (!in_array($origin,['http://127.0.0.1:8790','http://localhost:8790'],true)) return new JsonResponse(['error'=>'invalid_origin'],403);
        $token=$this->sessionToken();
        if (!hash_equals($token,(string)$request->headers->get('X-EZS-CSRF',''))) return new JsonResponse(['error'=>'csrf'],403);
        if ((string)$request->request->get('confirmation','') !== 'MAINTENANCE') return new JsonResponse(['error'=>'confirmation_required'],400);
        $root=dirname(__DIR__, 4);
        $python='H:/Python/pythoncore-3.14-64/python.exe';
        $code='from config.loader import load_runtime_config; from gateway_manager.manager import GatewayManager; g=GatewayManager(load_runtime_config()); s=g.set_maintenance(True); assert s.maintenance is True and s.http_alive';
        $process=new Process([$python,'-c',$code],$root,null,null,12);
        $process->run();
        if (!$process->isSuccessful()) return new JsonResponse(['error'=>'maintenance_failed'],503);
        $logdir=$root.'/runtime/prod-control';
        if (!is_dir($logdir)) mkdir($logdir,0700,true);
        file_put_contents($logdir.'/audit.log',gmdate('c')." action=maintenance origin=loopback result=ok\n",FILE_APPEND|LOCK_EX);
        return new JsonResponse(['status'=>'maintenance'],200,['Cache-Control'=>'no-store']);
    }
}
