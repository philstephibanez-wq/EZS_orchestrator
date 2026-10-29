<?php
declare(strict_types=1);

use Symfony\Bundle\FrameworkBundle\Test\KernelTestCase;
use Symfony\Bundle\FrameworkBundle\Console\Application;
use Symfony\Component\Console\Tester\CommandTester;

final class SymfonyCommands010Test extends KernelTestCase
{
    public function testInfrastructureAndProdCommandsAreRegistered(): void
    {
        self::bootKernel();
        $application = new Application(self::$kernel);
        $application->setAutoExit(false);
        foreach (['ezs:gateway:preflight', 'ezs:gateway:monitor', 'ezs:infrastructure', 'ezs:prod:mode', 'ezs:dev:cleanup-stale'] as $name) {
            self::assertTrue($application->has($name), 'Commande Symfony manquante : ' . $name);
        }
    }

    public function testReadOnlyGatewayCandidatePreflight(): void
    {
        self::bootKernel();
        $application = new Application(self::$kernel);
        $application->setAutoExit(false);
        $tester = new CommandTester($application->find('ezs:gateway:preflight'));
        // Les fichiers candidats et Caddy peuvent être absents sur CI : tester le contrat de sortie, pas leur disponibilité.
        $tester->execute(['target'=>'candidate']);
        $payload = json_decode($tester->getDisplay(), true);
        self::assertIsArray($payload);
        self::assertSame('READ_ONLY', $payload['mode'] ?? null);
        self::assertFalse($payload['prod_cutover_authorized'] ?? true);
    }
}
