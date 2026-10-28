<?php
declare(strict_types=1);
$root=dirname(__DIR__);
if(trim((string)file_get_contents($root.'/VERSION'))!=='4.2c1')throw new RuntimeException('VERSION_MISMATCH');
$contract=(string)file_get_contents($root.'/docs/contracts/QUEUES_JOBS_MIGRATION_4_2C0.md');
foreach(['#1, #8, #11, #12, #15, #18','finalize_error','fencing','181/#182/#185','START/STOP','Messenger'] as $marker) {
    if(!str_contains($contract,$marker))throw new RuntimeException('CONTRACT_MISSING:'.$marker);
}
foreach(['scripts/start.ps1','scripts/stop.ps1'] as $path) {
    if(!is_file($root.'/'.$path))throw new RuntimeException('LIFECYCLE_MISSING:'.$path);
}
echo "EZS_QUEUE_MIGRATION_4_2C1_CONTRACT_OK\n";
