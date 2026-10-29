<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Coordination;

final class QueueRestAccess
{
    private const KEYS=['lab'=>'EZS_QUEUE_LAB_TOKEN','assistant'=>'EZS_QUEUE_ASSISTANT_TOKEN','ezscore'=>'EZS_QUEUE_EZSCORE_TOKEN'];

    public static function producerFor(?string $header, ?array $values=null): ?string
    {
        if (!is_string($header) || !preg_match('/^Bearer ([A-Za-z0-9._~+\/=-]{32,256})$/D',$header,$m)) return null;
        $found=null;
        foreach(self::KEYS as $producer=>$key){
            $expected=$values===null?(string)(getenv($key)?:''):(string)($values[$producer]??'');
            if(strlen($expected)<32 || strlen($expected)>256)continue;
            if(hash_equals($expected,$m[1])){
                if($found!==null)return null;
                $found=$producer;
            }
        }
        return $found;
    }
}
