<?php

declare(strict_types=1);

namespace Ezs\Web\Tests\Unit;

use Ezs\Web\Module\Coordination\QueueSongLabels;
use PHPUnit\Framework\TestCase;

final class QueueSongLabelsContractTest extends TestCase
{
    public function testValidLabelsAndUntrustedKeys(): void
    {
        $payload = json_encode([
            'schema' => 'ezstudio.lab.queue-labels.v1',
            'labels' => ['193' => 'Breakfast in America — Supertramp',
                '-1' => 'refusé', 'a' => 'refusé', '205' => 'La Bohème'],
        ], JSON_THROW_ON_ERROR | JSON_UNESCAPED_UNICODE);
        self::assertSame([193 => 'Breakfast in America — Supertramp', 205 => 'La Bohème'],
            QueueSongLabels::parse($payload));
    }

    public function testWrongSchemaIsRejected(): void
    {
        $this->expectException(\InvalidArgumentException::class);
        QueueSongLabels::parse('{"schema":"unknown","labels":{}}');
    }

    public function testInvalidJsonIsRejected(): void
    {
        $this->expectException(\JsonException::class);
        QueueSongLabels::parse('not-json');
    }
}
