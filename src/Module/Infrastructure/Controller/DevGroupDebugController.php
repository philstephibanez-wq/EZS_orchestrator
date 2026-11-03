<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Infrastructure\Controller;

use Ezs\Web\Module\Infrastructure\NativeSiteObservation;
use Symfony\Component\HttpFoundation\Request;
use Symfony\Component\HttpFoundation\Response;
use Symfony\Component\Routing\Attribute\Route;

/** DEV-only observation: no PID, commands, tokens or mutation. */
final class DevGroupDebugController
{
    public static function allowed(string $environment,string $host,string $ip):bool
    {
        return DevGroupOperationsController::allowed($environment,$host,$ip);
    }

    /** Legacy pure presentation helper, retained for existing diagnostic consumers. */
    public static function summary(array $states):array
    {
        $result=[];
        foreach(['dev'=>['ezscore_dev','ezscore_preview'],'lab'=>['lab'],'assistant'=>['assistant']] as $group=>$names){
            $members=[];
            foreach($names as $name)$members[$name]=(string)($states[$name]??'MISSING');
            $result[$group]=$members;
        }
        return $result;
    }

    private static function observeAssistant(NativeSiteObservation $observer): string
    {
        try { return $observer->observe('assistant')['state']; }
        catch (\Throwable) { return 'UNVERIFIED'; }
    }

    #[Route('/api/v2/infrastructure/dev-debug-native', name:'ezs_dev_group_debug_native', methods:['GET'])]
    public function native(Request $request):Response
    {
        if (!self::allowed((string)($_SERVER['APP_ENV']??getenv('APP_ENV')?:''),$request->getHost(),(string)$request->getClientIp())) {
            return new Response('forbidden',403,['Cache-Control'=>'no-store']);
        }
        try {
            $observer=new NativeSiteObservation();
            $result=['schema'=>'ezs.dev_group_native_debug.v1',
                'groups'=>[
                    'dev'=>['dev'=>$observer->observe('dev')['state']],
                    'lab'=>['lab'=>$observer->observe('lab')['state']],
                    'assistant'=>['assistant'=>self::observeAssistant($observer)],
                ], 'error'=>null];
        }catch(\Throwable $error){
            $result=['schema'=>'ezs.dev_group_native_debug.v1','groups'=>[],'error'=>'INVENTORY_UNAVAILABLE'];
        }
        return new Response(json_encode($result,JSON_THROW_ON_ERROR),200,[
            'Content-Type'=>'application/json; charset=UTF-8','Cache-Control'=>'no-store',
            'X-Content-Type-Options'=>'nosniff','X-Robots-Tag'=>'noindex, nofollow',
        ]);
    }
}
