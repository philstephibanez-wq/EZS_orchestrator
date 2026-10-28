<?php
$src=(string)file_get_contents(__DIR__.'/../src/Module/Gpu/GpuProbe.php');
foreach (['proc_open(',"'bypass_shell' => true", "'create_new_console' => false",'proc_terminate('] as $s) if (!str_contains($src,$s)) throw new RuntimeException('GPU_NO_CONSOLE_CONTRACT_FAILED:'.$s);
if(str_contains($src,'new Process(')) throw new RuntimeException('GPU_SHELL_REGRESSION');
echo "EZS_GPU_NO_CONSOLE_CONTRACT_OK\n";
