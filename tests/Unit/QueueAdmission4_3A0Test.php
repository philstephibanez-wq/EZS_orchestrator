<?php

declare(strict_types=1);

use Ezs\Web\Module\Coordination\QueueAdmission;
use Ezs\Web\Module\Coordination\GlobalQueueStore;
use PHPUnit\Framework\TestCase;

final class QueueAdmission4_3A0Test extends TestCase
{
    private function envelope(): array
    {
        return ['external_id' => 'new-lab-job-900001', 'idempotency_key' => 'lab:900001:v1',
            'kind' => 'profile', 'resource_class' => 'cpu', 'priority' => 50];
    }

    public function testValidatesStrictTechnicalEnvelope(): void
    {
        self::assertSame($this->envelope(), QueueAdmission::parse($this->envelope()));
        foreach ([['producer'=>'assistant'], ['payload'=>['audio'=>'private']], ['priority'=>'50'],
            ['resource_class'=>'dangerous'], ['external_id'=>''], ['kind'=>str_repeat('x',129)]] as $change) {
            $invalid = array_replace($this->envelope(), $change);
            try {
                QueueAdmission::parse($invalid);
                self::fail('Unexpected admission for '.json_encode($change));
            } catch (\InvalidArgumentException $e) {
                self::assertNotSame('', $e->getMessage());
            }
        }
    }

    public function testIdempotenceAndConflictsOnTemporaryQueueOnly(): void
    {
        if (!extension_loaded('pdo_sqlite')) self::markTestSkipped('pdo_sqlite_required');
        $path = tempnam(sys_get_temp_dir(), 'ezs-admission-');
        self::assertIsString($path);
        try {
            $q = new GlobalQueueStore($path);
            $e = QueueAdmission::parse($this->envelope());
            $a = $q->enqueue('lab',$e['external_id'],$e['idempotency_key'],$e['kind'],$e['resource_class'],$e['priority']);
            $b = $q->enqueue('lab',$e['external_id'],$e['idempotency_key'],$e['kind'],$e['resource_class'],$e['priority']);
            self::assertSame($a['id'], $b['id']);
            self::assertSame('queued', $b['state']);
            self::assertSame('lab', QueueAdmission::publicRow($b)['producer']);
            self::assertArrayNotHasKey('lease_token', QueueAdmission::publicRow($b));
            self::assertArrayNotHasKey('idempotency_key', QueueAdmission::publicRow($b));
            try {
                $q->enqueue('lab',$e['external_id'],'different-key',$e['kind'],$e['resource_class'],$e['priority']);
                self::fail('Collision should be rejected');
            } catch (\DomainException) {
                self::assertTrue(true);
            }
        } finally {
            unset($q);
            foreach ([$path, $path.'-wal', $path.'-shm'] as $file) {
                if (is_file($file)) unlink($file);
            }
        }
    }

    public function testControllerAndInterfaceNeverTriggerAClaim(): void
    {
        $root = dirname(__DIR__,2);
        $controller = file_get_contents($root.'/src/Module/Coordination/Controller/QueueAdmissionController.php');
        $template = file_get_contents($root.'/templates/infrastructure/index.html.twig');
        self::assertIsString($controller);
        self::assertStringContainsString("methods: ['POST']",$controller);
        self::assertStringNotContainsString('->claim(', $controller);
        self::assertStringNotContainsString('->finish(', $controller);
        self::assertIsString($template);
        foreach (['dev-maintenance-button','dev-normal-button','prod-maintenance-button','prod-normal-button',
            'prod-maintenance-banner','dev-maintenance-banner','http-dev','http-prod','soft-dev','soft-prod'] as $id) {
            self::assertStringContainsString('id="'.$id.'"', $template);
        }
        self::assertStringContainsString('ezs-ezscore-cards.css', $template);
    }
}
