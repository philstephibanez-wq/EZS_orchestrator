from pathlib import Path
import ast
import unittest

ROOT = Path(__file__).resolve().parents[1]

class CaddyBootstrapAfterReboot(unittest.TestCase):
    def test_start_cmd_uses_launch_hidden(self):
        self.assertIn('launch.bat', (ROOT/'scripts/start.cmd').read_text(encoding='ascii'))
        self.assertIn('launch_hidden.ps1', (ROOT/'launch.bat').read_text(encoding='ascii'))

    def test_caddy_reconciliation_and_failure_isolation(self):
        source=(ROOT/'scripts/launch_hidden.ps1').read_text(encoding='utf-8-sig')
        self.assertIn('foreach ($target in @("dev", "prod", "lab"))', source)
        self.assertIn('-m caddy_manager.cli start --target $target', source)
        self.assertIn('caddy-start.log', source)
        self.assertIn('CADDY_DEV_NOT_READY', source)
        self.assertLess(source.index('-m service.service_cli restart-if-idle'), source.index('-m caddy_manager.cli start'))
        self.assertLess(source.index('-m caddy_manager.cli start'), source.index('Preserve-CurrentControlCenterToken'))
        self.assertNotIn('Stop-Process -Name caddy', source)

    def test_cli_start_must_report_http_ready(self):
        source=(ROOT/'caddy_manager/cli.py').read_text(encoding='utf-8')
        ast.parse(source)
        self.assertIn('args.command == "start" and not view.http_alive', source)

if __name__ == '__main__':
    unittest.main()
