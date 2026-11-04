<?php

declare(strict_types=1);

namespace Ezs\Web\Module\Coordination;

/** Disabled by default. The executor credential is distinct from producer credentials. */
final class QueueExecutorAccess
{
    public static function enabled(): bool
    {
        return self::configured('EZS_QUEUE_EXECUTOR_API') === '1';
    }

    public static function authorized(?string $authorization): bool
    {
        if (!self::enabled() || !is_string($authorization)
            || preg_match('#^Bearer ([A-Za-z0-9._~+/=\-]{32,256})$#D', $authorization, $matches) !== 1) {
            return false;
        }
        $expected = self::configured('EZS_QUEUE_EXECUTOR_TOKEN');
        if (!preg_match('#^[A-Za-z0-9._~+/=\-]{32,256}$#D', $expected)) {
            return false;
        }
        // A producer credential must never become an executor credential.
        if (QueueRestAccess::producerFor('Bearer '.$expected) !== null) {
            return false;
        }
        return hash_equals($expected, $matches[1]);
    }

    private static function configured(string $key): string
    {
        foreach ([getenv($key), $_SERVER[$key] ?? null, $_ENV[$key] ?? null] as $value) {
            if (is_string($value) && $value !== '') {
                return $value;
            }
        }
        return '';
    }
}
