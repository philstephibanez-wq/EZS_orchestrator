<?php
declare(strict_types=1);
$root = dirname(__DIR__);
$tpl = file_get_contents($root . '/templates/infrastructure/index.html.twig');
$panel = file_get_contents($root . '/templates/infrastructure/_gpu_monitor.html.twig');
$js = file_get_contents($root . '/public/assets/ezs-gpu-monitor.js');
$controller = file_get_contents($root . '/src/Module/Gpu/Controller/GpuDashboardController.php');
if (!str_contains($tpl, 'data-bs-theme="dark"') || !str_contains($tpl, "_gpu_monitor.html.twig") || !str_contains($tpl, "ezs-nav")) throw new RuntimeException('layout_invalid');
if (!str_contains($panel, 'ezs-performance-panel') || !str_contains($panel, '/api/v2/gpu/dashboard')) throw new RuntimeException('panel_invalid');
if (!str_contains($js, 'data-perf-line') || !str_contains($controller, "getClientIp()")) throw new RuntimeException('gpu_dashboard_invalid');
echo "GPU_DRAWER_CONTRACT_OK\n";
