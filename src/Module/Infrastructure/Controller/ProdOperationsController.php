<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Infrastructure\Controller;

use Symfony\Component\HttpFoundation\JsonResponse;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\Routing\Attribute\Route;

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

    private function backendReady(): bool
    {
        $context=stream_context_create(['http'=>[
            'timeout'=>2,
            'ignore_errors'=>true,
            'header'=>"Host: ezscore.logandplay.com\r\n",
        ]]);
        $body=@file_get_contents('http://127.0.0.1:8511/fr/catalog',false,$context);
        $status=$http_response_header[0] ?? '';
        return is_string($body) && strlen($body)>0
            && preg_match('~^HTTP/\\S+ [234]\\d\\d~',$status)===1;
    }

    #[Route('/api/v2/infrastructure/prod-control', name:'ezs_prod_control_read', methods:['GET'])]
    public function read(Request $request): JsonResponse
    {
        if (!$this->allowed($request)) return new JsonResponse(['error'=>'forbidden'],403);
        $token=$this->sessionToken();
        $config='H:/EZScore/var/runtime/online-gateway.json';
        $desired=null;
        if (is_file($config)) {
            $data=json_decode((string)file_get_contents($config),true);
            if (is_array($data) && is_bool($data['maintenance'] ?? null)) $desired=$data['maintenance'];
        }
        $gateway=null;
        $context=stream_context_create(['http'=>['timeout'=>1,'ignore_errors'=>true]]);
        $raw=@file_get_contents('http://127.0.0.1:8510/__ezscore_gateway_status',false,$context);
        if (is_string($raw)) {
            $data=json_decode($raw,true);
            if (is_array($data) && ($data['protocol'] ?? '')==='ezscore.online-gateway.v3' && ($data['ok'] ?? false)===true) $gateway=$data;
        }
        $socket=@stream_socket_client('tcp://127.0.0.1:8501',$errno,$errstr,0.5);
        $caddy=is_resource($socket);
        if ($caddy) fclose($socket);
        $backend=$gateway!==null && $caddy && $this->backendReady();
        return new JsonResponse([
            'schema'=>'ezs.prod_control.v1',
            'gateway_online'=>$gateway!==null,
            'caddy_listening'=>$caddy,
            'backend_ready'=>$backend,
            'maintenance'=>$gateway['maintenance'] ?? null,
            'desired_maintenance'=>$desired,
            'csrf'=>$token,
            'actions'=>[
                'maintenance'=>$gateway!==null && $caddy && ($gateway['maintenance'] ?? null)===false,
                'normal'=>$backend && ($gateway['maintenance'] ?? null)===true,
            ],
            'note'=>$backend?'Backend Symfony accessible depuis Caddy interne.':'Mode normal indisponible : backend Symfony non vérifié.',
        ],200,['Cache-Control'=>'no-store']);
    }

    #[Route('/api/v2/infrastructure/prod-control/{action}', name:'ezs_prod_control_action', requirements:['action'=>'maintenance|normal'], methods:['POST'])]
    public function action(Request $request,string $action): JsonResponse
    {
        if (!$this->allowed($request)) return new JsonResponse(['error'=>'forbidden'],403);
        $origin=$request->headers->get('Origin','');
        if (!in_array($origin,['http://127.0.0.1:8790','http://localhost:8790'],true)) return new JsonResponse(['error'=>'invalid_origin'],403);
        $token=$this->sessionToken();
        if (!hash_equals($token,(string)$request->headers->get('X-EZS-CSRF',''))) return new JsonResponse(['error'=>'csrf'],403);
        $expected=$action==='normal'?'NORMAL':'MAINTENANCE';
        if ((string)$request->request->get('confirmation','')!==$expected) return new JsonResponse(['error'=>'confirmation_required'],400);
        if ($action==='normal' && !$this->backendReady()) return new JsonResponse(['error'=>'prod_backend_unavailable'],503);
        $script=dirname(__DIR__,4).'/scripts/prod_lifecycle.ps1';
        if (!is_file($script)) return new JsonResponse(['error'=>'prod_lifecycle_missing'],503);
        if (!function_exists('proc_open')) return new JsonResponse(['error'=>'proc_open_unavailable'],503);
        $cmd=['powershell.exe','-NoProfile','-NonInteractive','-ExecutionPolicy','Bypass','-File',$script,'-Action',$action];
        $pipes=[];
        $process=@proc_open($cmd,[0=>['pipe','r'],1=>['pipe','w'],2=>['pipe','w']],$pipes,dirname(__DIR__,4));
        if (!is_resource($process)) return new JsonResponse(['error'=>'prod_lifecycle_launch_failed'],503);
        fclose($pipes[0]);
        $stdout=stream_get_contents($pipes[1]); fclose($pipes[1]);
        $stderr=stream_get_contents($pipes[2]); fclose($pipes[2]);
        $exit=proc_close($process);
        if ($exit!==0) return new JsonResponse(['error'=>'prod_lifecycle_refused','detail'=>mb_substr(trim((string)$stderr),0,500)],503,['Cache-Control'=>'no-store']);
        $marker=$action==='normal'?'EZS_PROD_NORMAL_REQUESTED_VERIFY_SSO_MEDIA':'EZS_PROD_MAINTENANCE_OK';
        if (!str_contains((string)$stdout,$marker)) return new JsonResponse(['error'=>'prod_lifecycle_unconfirmed'],503);
        return new JsonResponse(['ok'=>true,'action'=>$action,'result'=>$marker],200,['Cache-Control'=>'no-store']);
    }
}
