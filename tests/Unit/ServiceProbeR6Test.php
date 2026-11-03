<?php
declare(strict_types=1);
namespace Ezs\Web\Tests\Unit;
use Ezs\Web\Module\Infrastructure\ServiceProbeR6 as Probe;
use PHPUnit\Framework\TestCase;
final class ServiceProbeR6Test extends TestCase
{
    public function testProd404IsFatalOnlyWhenMandatoryEndpoint(): void
    {
        self::assertSame('FATAL',Probe::classifySoft('prod',404,null,null)['state']);
        self::assertSame('ERROR',Probe::classifySoft('dev',404,null,null)['state']);
        self::assertSame('ERROR',Probe::classifySoft('lab',404,null,null)['state']);
        self::assertSame('ERROR',Probe::classifySoft('assistant',404,null,null)['state']);
    }
    public function testCutoverNeedsIntentAndVerifiedOwnership(): void
    {
        $soft=Probe::classifySoft('prod',404,null,null);
        self::assertFalse(Probe::fatalCutoverCandidate('prod','RUNNING',$soft,false));
        self::assertFalse(Probe::fatalCutoverCandidate('prod','STOPPED',$soft,true));
        self::assertTrue(Probe::fatalCutoverCandidate('prod','RUNNING',$soft,true));
        self::assertFalse(Probe::fatalCutoverCandidate('dev','RUNNING',$soft,true));
    }
    public function testValidJsonAndCollectionFailure(): void
    {
        $ok=['schema'=>'ezs.service-status.v1','state'=>'OK','components'=>[]];
        self::assertSame('OK',Probe::classifySoft('prod',200,$ok,null)['state']);
        self::assertSame('ERROR',Probe::classifySoft('prod',200,[],null)['state']);
        self::assertSame('COLLECTION_ERROR',Probe::classifySoft('prod',0,null,'SOFT_REQUEST_FAILED')['state']);
    }
}
