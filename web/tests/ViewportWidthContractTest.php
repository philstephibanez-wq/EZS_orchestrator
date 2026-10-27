<?php
declare(strict_types=1);
$css=file_get_contents(dirname(__DIR__).'/public/assets/ezs-infrastructure.css');
foreach (['width: calc(100% - var(--ezs-perf-width))','box-sizing: border-box','min-width: 0','@media (max-width: 1000px)'] as $needed) {
  if (!str_contains($css,$needed)) throw new RuntimeException('missing_viewport_rule: '.$needed);
}
echo "VIEWPORT_WIDTH_OK\n";
