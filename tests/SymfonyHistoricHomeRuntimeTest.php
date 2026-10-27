<?php
declare(strict_types=1);
$root = dirname(__DIR__);
require $root.'/vendor/autoload.php';
$kernel = new \Ezs\Web\Kernel('dev', true);
try {
    $kernel->boot();
    foreach ([
        ['/',200,['EZS Orchestrator','ezs-performance-panel','DEV · EZScore','PROD · EZScore','LAB · EZStudio','Assistant']],
        ['/api/status',200,['symfony_root','migration']],
        ['/api/jobs',503,['jobs_migration_pending']],
    ] as [$path,$expected,$markers]) {
        $request = \Symfony\Component\HttpFoundation\Request::create(
            $path,'GET',[],[],[],['HTTP_HOST'=>'127.0.0.1','REMOTE_ADDR'=>'127.0.0.1']
        );
        $response = $kernel->handle($request);
        try {
            if($response->getStatusCode()!==$expected)throw new RuntimeException('STATUS_'.$path.'_'.$response->getStatusCode());
            foreach($markers as $marker) {
                if(!str_contains((string)$response->getContent(),$marker))throw new RuntimeException('MARKER_'.$path.'_'.$marker);
            }
        } finally { $kernel->terminate($request,$response); }
    }
    echo "SYMFONY_HISTORIC_HOME_RUNTIME_OK\n";
} finally {$kernel->shutdown();}
