<?php
declare(strict_types=1);

$root = dirname(__DIR__);
$template = file_get_contents($root . '/templates/infrastructure/index.html.twig');
$script = file_get_contents($root . '/public/assets/ezs-infrastructure.js');
if (!str_contains($template, 'bootstrap@5.3.3') || !str_contains($template, 'jquery-3.7.1.min.js')) {
    throw new RuntimeException('ui_dependencies_missing');
}
if (!str_contains($template, 'refresh-environments') || !str_contains($script, '/api/v2/environments')) {
    throw new RuntimeException('ui_rest_binding_missing');
}
if (str_contains($script, '.html(') || !str_contains($script, '.text(')) {
    throw new RuntimeException('unsafe_dom_rendering');
}
echo "EZS_UI_STANDARD_OK\n";
