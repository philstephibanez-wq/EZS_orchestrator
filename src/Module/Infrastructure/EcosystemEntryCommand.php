<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Infrastructure;
use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;
#[AsCommand(name:'ezs:ecosystem:start',description:'Démarrage DEV par API Windows native, sans PowerShell')]
final class EcosystemEntryCommand extends Command
{
    protected function configure():void {$this->addOption('plan',null,InputOption::VALUE_NONE);}
    protected function execute(InputInterface $input,OutputInterface $output):int {return self::invoke('start',(bool)$input->getOption('plan'),$output);}
    /** Callbacks optionnels pour vérifier la coordination sans démarrer de processus réels. */
    public static function invoke(string $action,bool $plan,OutputInterface $output,?callable $devStart=null,?callable $aiStart=null):int
    {
        if(!in_array($action,['start','stop'],true)){ $output->writeln('EZS_ECOSYSTEM_ACTION_REFUSED');return Command::INVALID; }
        if($plan){
            $output->writeln('EZS_ECOSYSTEM_PLAN='.strtoupper($action));
            $output->writeln('EZS_ECOSYSTEM_ENGINE=NATIVE_WINDOWS_WMI');
            if($action==='start')$output->writeln('EZS_ECOSYSTEM_AI_START=LOCAL_AI_LIFECYCLE_8720');
            return Command::SUCCESS;
        }
        try{
            $svc=new NativeWindowsLifecycle();
            $result=$action==='start' ? ($devStart ?? static fn():array=>$svc->start())() : $svc->stop();
            foreach($result as $name=>$pid)$output->writeln('EZS_NATIVE_'.strtoupper($action).'='.$name.' PID='.$pid);
            $output->writeln('EZS_NATIVE_DEV_'.strtoupper($action).'_OK');
            if($action==='start'){
                $output->writeln('EZS_PROD_STATUS=NOT_MANAGED_BY_THIS_COMMAND');
                try{
                    $ai=($aiStart ?? static fn():array=>(new LocalAiLifecycle())->start())();
                    if(!is_array($ai) || !is_int($ai['pid']??null) || $ai['pid']<1 || !in_array($ai['action']??null,['STARTED','ALREADY_READY'],true))
                        throw new \RuntimeException('EZS_AI_RESULT_INVALID');
                    $output->writeln('EZS_AI_START_OWNED_READY_8720 PID='.$ai['pid'].' ACTION='.$ai['action']);
                }catch(\Throwable $e){
                    // DEV n'est jamais arrêté en compensation : état partiel explicite.
                    $output->writeln('<error>EZS_ECOSYSTEM_PARTIAL_DEV_READY_AI_REFUSED:'.$e->getMessage().'</error>');
                    return Command::FAILURE;
                }
            }
            return Command::SUCCESS;
        }catch(\Throwable $e){$output->writeln('<error>EZS_NATIVE_'.strtoupper($action).'_REFUSED:'.$e->getMessage().'</error>');return Command::FAILURE;}
    }
}
