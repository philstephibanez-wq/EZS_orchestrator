<?php

declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use PHPUnit\Framework\TestCase;
use Twig\Environment;
use Twig\Loader\FilesystemLoader;

final class JobsPageSingleQueueContractTest extends TestCase
{
    private function template(): string
    {
        return dirname(__DIR__, 2) . '/templates/jobs/index.html.twig';
    }

    public function testSingleGlobalAuthorityAndCurrentQueueOnly(): void
    {
        $template = file_get_contents($this->template());
        self::assertIsString($template);
        self::assertStringContainsString('Queue globale — Orchestrator (autorité)', $template);
        self::assertStringContainsString('global_queue.jobs', $template);
        self::assertStringNotContainsString('Jobs LAB — vue du producteur (REST, lecture seule)', $template);
        self::assertStringNotContainsString('lab_queue.jobs', $template);
        self::assertStringContainsString('<th>Chanson</th>', $template);
        self::assertStringContainsString('job.song_title', $template);
        self::assertStringContainsString('Les archives V1 sont conservées', $template);
        self::assertStringNotContainsString('<strong>Dernières tentatives archivées V1</strong>', $template);
        self::assertStringNotContainsString('recoverExpired(', $template);
        self::assertStringNotContainsString('claim(', $template);
        self::assertStringNotContainsString('window.location.reload()', $template);
    }

    public function testJobsPageTemplateParsesWithoutRuntimeDependencies(): void
    {
        $loader = new FilesystemLoader(dirname(__DIR__, 2) . '/templates');
        $twig = new Environment($loader, ['strict_variables' => true]);
        $source = file_get_contents($this->template());
        self::assertIsString($source);
        $twig->parse($twig->tokenize(new \Twig\Source($source, 'jobs/index.html.twig')));
        self::assertTrue(true);
    }
}
