<?php
declare(strict_types=1);
$r=dirname(__DIR__);
if(trim((string)file_get_contents($r.'/VERSION'))!=='2.5a0')throw new RuntimeException('VERSION');
$c=(string)file_get_contents($r.'/docs/contracts/FILES_JOBS_V2_5A0.md');
foreach(['Orchestrator #8','Orchestrator #15','LAB #16','Messenger','fencing','181/182/185','Assistant','EZScore'] as $s){if(!str_contains($c,$s))throw new RuntimeException('CONTRACT_MISSING:'.$s);}
echo "EZS_FILES_JOBS_2_5A0_CONTRACT_OK\n";