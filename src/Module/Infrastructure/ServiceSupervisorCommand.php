<?php
declare(strict_types=1);

namespace Ezs\Web\Module\Infrastructure;

use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputArgument;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Output\OutputInterface;

/** Exécution ponctuelle : le planificateur Windows l'appelle indépendamment du serveur web. */
#[AsCommand(name:'ezs:services',description:'État désiré, START/STOP et supervision native indépendante')]
final class ServiceSupervisorCommand extends Command
{
    private const ROOT='H:/EZS_orchestrator';
    private const GROUPS=['root','dev','lab','assistant','prod'];
    private const RETRY=self::ROOT.'/runtime/supervision/retry.json';
    private const LOG=self::ROOT.'/var/log/supervision/events.log';

    protected function configure():void
    {
        $this->addArgument('action',InputArgument::REQUIRED,'status|tick|diagnostics|start|stop|restart')
             ->addArgument('group',InputArgument::OPTIONAL,'root|dev|lab|assistant|prod');
    }

    private static function native(string $group):NativeWindowsLifecycle
    {
        return new NativeWindowsLifecycle(profile:$group==='prod'?'prod':'dev');
    }

    public static function nextAttempt(int $failures,int $now):int
    {
        return $now+min(300,30*(2**min(4,max(0,$failures-1))));
    }

    public static function planned(array $desired):array
    {
        $plan=[];
        foreach(self::GROUPS as $group){
            if($group==='root')continue; // ROOT belongs to the Windows watchdog.
            if(($desired[$group]??DesiredServiceState::STOPPED)===DesiredServiceState::RUNNING)$plan[]=$group;
        }
        return $plan;
    }

    private static function log(string $level,string $group,string $event):void
    {
        $dir=dirname(self::LOG);
        if(!is_dir($dir)&&!mkdir($dir,0700,true)&&!is_dir($dir))throw new \RuntimeException('EZS_SUPERVISOR_LOG_DIR_FAILED');
        $event=substr(preg_replace('/[\r\n\x00-\x1f]/',' ', $event)??'unknown',0,300);
        $line=gmdate('c').' '.$level.' '.$group.' '.$event."\n";
        if(file_put_contents(self::LOG,$line,FILE_APPEND|LOCK_EX)===false)throw new \RuntimeException('EZS_SUPERVISOR_LOG_WRITE_FAILED');
    }

    private static function retryRead():array
    {
        if(!is_file(self::RETRY))return [];
        $data=json_decode((string)file_get_contents(self::RETRY),true);
        if(!is_array($data)||($data['schema']??null)!=='ezs.supervisor.retry.v1'||!is_array($data['groups']??null))
            throw new \RuntimeException('EZS_SUPERVISOR_RETRY_INVALID');
        return $data['groups'];
    }

    private static function retrySave(array $data):void
    {
        $dir=dirname(self::RETRY);
        if(!is_dir($dir)&&!mkdir($dir,0700,true)&&!is_dir($dir))throw new \RuntimeException('EZS_SUPERVISOR_STATE_DIR_FAILED');
        $tmp=self::RETRY.'.'.bin2hex(random_bytes(8)).'.tmp';
        $json=json_encode(['schema'=>'ezs.supervisor.retry.v1','groups'=>$data],JSON_THROW_ON_ERROR|JSON_PRETTY_PRINT)."\n";
        try{
            if(file_put_contents($tmp,$json,LOCK_EX)!==strlen($json)||!rename($tmp,self::RETRY))
                throw new \RuntimeException('EZS_SUPERVISOR_STATE_WRITE_FAILED');
        } finally {if(is_file($tmp))unlink($tmp);}
    }

    private static function runOne(string $group):array
    {
        if ($group === 'assistant') {
            $web = self::native('assistant')->reconcileFastCgiGroup('assistant', true);
            $ai = AssistantDependencyLifecycle::ensureRunning();
            return $web + $ai;
        }
        return self::native($group)->reconcileFastCgiGroup($group, true);
    }

    private static function stopOne(string $group):array
    {
        if ($group === 'assistant') {
            // A failure to attest the AI must not be hidden by stopping the web interface.
            $ai = AssistantDependencyLifecycle::stopOwned();
            return $ai + self::native('assistant')->reconcileFastCgiGroup('assistant', false);
        }
        return self::native($group)->reconcileFastCgiGroup($group, false);
    }

    private static function tick(OutputInterface $output):int
    {
        $dir=self::ROOT.'/runtime/supervision';
        if(!is_dir($dir)&&!mkdir($dir,0700,true)&&!is_dir($dir))throw new \RuntimeException('EZS_SUPERVISOR_DIR_FAILED');
        $lock=fopen($dir.'/tick.lock','c+');
        if(!is_resource($lock)||!flock($lock,LOCK_EX|LOCK_NB)){
            if(is_resource($lock))fclose($lock);
            $output->writeln('EZS_SUPERVISOR_TICK_ALREADY_RUNNING');
            return Command::SUCCESS;
        }
        try{
            $desired=(new DesiredServiceState())->all();
            $retry=self::retryRead();
            // Enforce STOPPED even if orphan FastCGI survived a previous stop.
            foreach (['dev','lab','assistant','prod'] as $stoppedGroup) {
                if (($desired[$stoppedGroup]??DesiredServiceState::STOPPED)!==DesiredServiceState::STOPPED) continue;
                try { self::stopOne($stoppedGroup); }
                catch (\Throwable $e) { self::log('ERROR',$stoppedGroup,'STOP_CLEANUP_FAILED '.$e->getMessage()); }
            }
            $tickBegin=hrtime(true);
            $result=ServiceSupervisorCycle::run(
                $desired,
                $retry,
                time(),
                static function(string $group) use ($output):array {
                    $t=hrtime(true);
                    try {return self::runOne($group);}
                    finally {$output->writeln('EZS_TIMING_GROUP_'.$group.'_MS='.round((hrtime(true)-$t)/1000000,2));}
                },
                self::log(...),
                self::retrySave(...),
                static fn(string $line): mixed => $output->writeln($line)
            );
            // ROOT est supervisé par le watchdog. Nettoyer seulement un ancien ROOT
            // sans port si un ROOT actif est atteste sur 8791.
            if (($desired['root']??null)===DesiredServiceState::RUNNING) {
                $cleanupBegin=hrtime(true);
                $cleaned=(new NativeWindowsLifecycle())->cleanupRootResidual();
                foreach ($cleaned as $pid) {
                    $output->writeln('EZS_ROOT_RESIDUAL_CLEANED_PID='.$pid);
                }
                $output->writeln('EZS_TIMING_ROOT_CLEANUP_MS='.round((hrtime(true)-$cleanupBegin)/1000000,2));
            }
            $output->writeln('EZS_TIMING_TICK_TOTAL_MS='.round((hrtime(true)-$tickBegin)/1000000,2));
            return $result;
        }finally{flock($lock,LOCK_UN);fclose($lock);}
    }

    protected function execute(InputInterface $input,OutputInterface $output):int
    {
        $action=(string)$input->getArgument('action');
        $group=(string)($input->getArgument('group')??'');
        if(!in_array($action,['status','tick','diagnostics','start','stop','restart'],true)||
            ($action!=='status'&&$action!=='tick'&&$action!=='diagnostics'&&!in_array($group,self::GROUPS,true)))
            return Command::INVALID;
        try{
            $intent=new DesiredServiceState();
            if($action==='status'){
                foreach($intent->all() as $name=>$state)$output->writeln($name.'='.$state);
                return Command::SUCCESS;
            }
            if($action==='diagnostics') {
                $rows=[];
                foreach (['dev','prod'] as $profile) {
                    foreach ((new NativeWindowsLifecycle(profile:$profile))->fastCgiProcessReport() as $item) {
                        $pid=(int)$item['pid'];
                        if (!isset($rows[$pid]) || ($rows[$pid]['service']==='UNVERIFIED' && $item['service']!=='UNVERIFIED')) {
                            $rows[$pid]=$item;
                        }
                    }
                }
                ksort($rows,SORT_NUMERIC);
                foreach ($rows as $r) {
                    $output->writeln('EZS_PHP_CGI PID='.$r['pid'].' STATE='.$r['state'].' SERVICE='.$r['service'].' PORTS='.implode(',',$r['ports']));
                }
                $output->writeln('EZS_PHP_CGI_TOTAL='.count($rows));
                return Command::SUCCESS;
            }
            if($action==='tick')return self::tick($output);
            // Persist first; on failure the supervisor will continue recovery only for RUNNING.
            $intent->set($group,$action==='stop'?DesiredServiceState::STOPPED:DesiredServiceState::RUNNING);
            if($action==='stop')$result=self::stopOne($group);
            elseif($action==='restart'){
                self::stopOne($group);
                $result=self::runOne($group);
            }else $result=self::runOne($group);
            $output->writeln('EZS_SERVICES_'.strtoupper($action).'_'.$group.'_OK processes='.count($result));
            return Command::SUCCESS;
        }catch(\Throwable $failure){
            $output->writeln('<error>EZS_SERVICES_REFUSED '.$failure->getMessage().'</error>');
            return Command::FAILURE;
        }
    }
}
