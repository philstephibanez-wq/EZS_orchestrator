from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'

class R334StandardStartStopContract(unittest.TestCase):
    def test_version_remains_1_2m(self):
        self.assertEqual('1.2o', (ROOT / 'VERSION').read_text(encoding='utf-8-sig').strip())

    def test_canonical_start_exists(self):
        path = SCRIPTS / 'start.cmd'
        self.assertTrue(path.is_file())
        text = path.read_text(encoding='ascii')
        self.assertIn('call "%~dp0..\\launch.bat"', text)

    def test_canonical_stop_exists(self):
        path = SCRIPTS / 'stop.cmd'
        self.assertTrue(path.is_file())
        text = path.read_text(encoding='ascii')
        self.assertIn('stop_orchestrator.ps1', text)
        self.assertNotIn('..\\stop.bat', text)

    def test_legacy_entrypoints_preserved(self):
        self.assertTrue((ROOT / 'launch.bat').is_file())
        self.assertTrue((ROOT / 'stop.bat').is_file())

if __name__ == '__main__':
    unittest.main()
