<?php
declare(strict_types=1);

$directory = __DIR__;
$manifest = require $directory . '/manifest.php';
if (!is_array($manifest) || $manifest === []) {
    fwrite(STDERR, "EZS_TEST_MANIFEST_EMPTY\n");
    exit(1);
}
$registered = [];
$previous = 0;
foreach ($manifest as $number => $file) {
    $order = (int) $number;
    if ($order <= $previous || !is_string($file)
        || !preg_match('/^\d{3}_[A-Za-z0-9_]+Test\.php$/D', $file)
        || !str_starts_with($file, sprintf('%03d_', $order))
        || !is_file($directory . DIRECTORY_SEPARATOR . $file)) {
        fwrite(STDERR, "EZS_TEST_MANIFEST_INVALID:" . (string) $file . "\n");
        exit(1);
    }
    $registered[] = $file;
    $previous = $order;
}
$found = [];
foreach (new DirectoryIterator($directory) as $item) {
    if ($item->isFile() && preg_match('/Test\.php$/D', $item->getFilename())) {
        $found[] = $item->getFilename();
    }
}
sort($registered);
sort($found);
$unlisted = array_values(array_diff($found, $registered));
if ($unlisted !== []) {
    fwrite(STDERR, 'EZS_TEST_UNREGISTERED:' . implode(',', $unlisted) . "\n");
    exit(1);
}
$failures = 0;
foreach ($manifest as $number => $file) {
    echo 'TEST ' . $number . ' ' . $file . "\n";
    $process = proc_open([PHP_BINARY, $directory . DIRECTORY_SEPARATOR . $file],
        [0 => ['pipe', 'r'], 1 => STDOUT, 2 => STDERR], $pipes, dirname($directory));
    if (!is_resource($process)) {
        ++$failures;
        echo 'FAIL ' . $number . ' process unavailable' . "\n";
        continue;
    }
    fclose($pipes[0]);
    $exit = proc_close($process);
    if ($exit !== 0) {
        ++$failures;
        echo 'FAIL ' . $number . ' exit=' . $exit . "\n";
    }
}
echo 'EZS_TESTS_TOTAL=' . count($manifest) . "\n";
echo 'EZS_TESTS_FAILED=' . $failures . "\n";
exit($failures === 0 ? 0 : 1);
