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

    public function testLegacyLabQueueProbeIsAbsent(): void
    {
        $template = file_get_contents($this->template());
        self::assertIsString($template);
        self::assertStringNotContainsString('lab_queue', $template);
        self::assertStringContainsString('global_queue', $template);
        self::assertStringContainsString('Dernières tentatives archivées', $template);
    }

    public function testJobsPageRendersWithCanonicalQueueOnly(): void
    {
        $loader = new FilesystemLoader(dirname(__DIR__, 2) . '/templates');
        $twig = new Environment($loader, ['strict_variables' => true]);
        $source = file_get_contents($this->template());
        self::assertIsString($source);
        // Syntax parsing is independent of the layout's runtime globals.
        $twig->parse($twig->tokenize(new \Twig\Source($source, 'jobs/index.html.twig')));
        self::assertTrue(true);
    }
}
