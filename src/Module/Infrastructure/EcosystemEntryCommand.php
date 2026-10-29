<?php
declare(strict_types=1);

namespace Ezs\Web\Module\Infrastructure;

use Symfony\Component\Console\Attribute\AsCommand;
use Symfony\Component\Console\Command\Command;
use Symfony\Component\Console\Input\InputInterface;
use Symfony\Component\Console\Input\InputOption;
use Symfony\Component\Console\Output\OutputInterface;
use Symfony\Component\Process\Process;

/** Entrée CLI Symfony de transition : le moteur PowerShell existant reste autorité. */
#[AsCommand(name: 'ezs:ecosystem:start', description: 'Démarrer selon le contrat START existant')]
final class EcosystemEntryCommand extends Command
{
    protected function configure(): void
    {
        $this->addOption('plan', null, InputOption::VALUE_NONE, 'Afficher sans exécuter');
    }

    protected function execute(InputInterface $input, OutputInterface $output): int
    {
        return self::invoke('start', (bool) $input->getOption('plan'), $output);
    }

    public static function invoke(string $action, bool $plan, OutputInterface $output): int
    {
        if (!in_array($action, ['start', 'stop'], true)) {
            $output->writeln('<error>EZS_ECOSYSTEM_ACTION_REFUSED</error>');
            return Command::INVALID;
        }
        $root = dirname(__DIR__, 3);
        $script = $root . '/scripts/' . $action . '.ps1';
        if (!is_file($script)) {
            $output->writeln('<error>EZS_ECOSYSTEM_SCRIPT_MISSING</error>');
            return Command::FAILURE;
        }
        if ($plan) {
            $output->writeln('EZS_ECOSYSTEM_PLAN=' . strtoupper($action));
            $output->writeln('EZS_ECOSYSTEM_ENGINE=LEGACY_POWERSHELL_TRANSITION');
            return Command::SUCCESS;
        }
        if (PHP_OS_FAMILY !== 'Windows') {
            $output->writeln('<error>EZS_ECOSYSTEM_WINDOWS_REQUIRED</error>');
            return Command::FAILURE;
        }
        $process = new Process(['powershell.exe', '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', $script], $root);
        $process->setTimeout(900);
        try {
            $process->run(static function (string $type, string $buffer) use ($output): void {
                $output->write($buffer);
            });
        } catch (\Throwable $e) {
            $output->writeln('<error>EZS_ECOSYSTEM_PROCESS_FAILED: ' . $e->getMessage() . '</error>');
            return Command::FAILURE;
        }
        return $process->isSuccessful() ? Command::SUCCESS : Command::FAILURE;
    }
}
