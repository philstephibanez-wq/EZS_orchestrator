<?php
declare(strict_types=1);
namespace Ezs\Web\Module\Infrastructure;

use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;

#[AsCommand(name: 'ezs:ecosystem:stop', description: 'Arrêter DEV seulement (PROD préservée)')]
final class EcosystemStopCommand extends Command
{
    protected function configure(): void { $this->addOption('plan', null, InputOption::VALUE_NONE, 'Afficher sans exécuter'); }
    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        return EcosystemEntryCommand::invoke('stop', (bool)$input->getOption('plan'), $output);
    }
}
