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
    public static function invoke(string $action,bool $plan,OutputInterface $output):int
    {
        if(!in_array($action,['start','stop'],true)){ $output->writeln('EZS_ECOSYSTEM_ACTION_REFUSED');return Command::INVALID; }
        if($plan){$output->writeln('EZS_ECOSYSTEM_PLAN='.strtoupper($action));$output->writeln('EZS_ECOSYSTEM_ENGINE=NATIVE_WINDOWS_WMI');return Command::SUCCESS;}
        try{
            $svc=new NativeWindowsLifecycle();
            $result=$action==='start'?$svc->start():$svc->stop();
            foreach($result as $name=>$pid)$output->writeln('EZS_NATIVE_'.strtoupper($action).'='.$name.' PID='.$pid);
            $output->writeln('EZS_NATIVE_DEV_'.strtoupper($action).'_OK');
            if($action==='start')$output->writeln('EZS_PROD_STATUS=NOT_MANAGED_BY_THIS_COMMAND');
            return Command::SUCCESS;
        }catch(\Throwable $e){$output->writeln('<error>EZS_NATIVE_'.strtoupper($action).'_REFUSED:'.$e->getMessage().'</error>');return Command::FAILURE;}
    }
}
