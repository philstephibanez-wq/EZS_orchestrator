<?php
declare(strict_types=1);
$r=dirname(__DIR__);
if(trim((string)file_get_contents($r.'/VERSION'))!=='4.2c5')throw new RuntimeException('VERSION');
$base=(string)file_get_contents($r.'/templates/layout/base.html.twig');
foreach(['_gpu_monitor.html.twig','ezs-gpu-monitor.js','orchestrator_version','aria-current="page"','block content','block page_scripts'] as $needle)if(!str_contains($base,$needle))throw new RuntimeException('LAYOUT_MISSING:'.$needle);
foreach(['infrastructure/index.html.twig','jobs/index.html.twig'] as $path){
 $source=(string)file_get_contents($r.'/templates/'.$path);
 if(!str_contains($source,"{% extends 'layout/base.html.twig' %}"))throw new RuntimeException('NOT_EXTENDING_LAYOUT:'.$path);
 if(str_contains($source,'<html')||str_contains($source,'<body'))throw new RuntimeException('DUPLICATED_SHELL:'.$path);
}
$jobsController=(string)file_get_contents($r.'/src/Module/Coordination/Controller/JobsPageController.php');
if(!str_contains($jobsController,"'active_page' => 'jobs'")||!str_contains($jobsController,"'orchestrator_version' => $version"))throw new RuntimeException('JOBS_CONTEXT_MISSING');
echo "EZS_SHARED_LAYOUT_GPU_4_2C5_OK\n";
