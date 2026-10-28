<?php
declare(strict_types=1);
$root = dirname(__DIR__);
if (trim((string) file_get_contents($root . '/VERSION')) !== '4.2c14') {
    throw new RuntimeException('VERSION');
}
foreach (['layout/base.html.twig', 'infrastructure/index.html.twig', 'jobs/index.html.twig'] as $view) {
    $source = (string) file_get_contents($root . '/templates/' . $view);
    if (preg_match('/\\bMAIN\\b/u', $source)) {
        throw new RuntimeException('MAIN_VISIBLE_IN_' . $view);
    }
}
echo "EZS_UI_LABELS_4_2C14_OK\n";
