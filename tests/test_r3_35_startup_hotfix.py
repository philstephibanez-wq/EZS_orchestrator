from pathlib import Path
import py_compile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class R335StartupHotfixContract(unittest.TestCase):
    def test_version_remains_1_2m(self):
        self.assertEqual("1.2n", (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip())

    def test_manager_compiles(self):
        py_compile.compile(str(ROOT / "assistant_supervision" / "manager.py"), doraise=True)

    def test_canonical_start(self):
        text = (ROOT / "scripts" / "start.cmd").read_text(encoding="ascii")
        self.assertIn("launch.bat", text)

    def test_canonical_stop_targets_control_center_and_service(self):
        cmd = (ROOT / "scripts" / "stop.cmd").read_text(encoding="ascii")
        ps = (ROOT / "scripts" / "stop_orchestrator.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("stop_orchestrator.ps1", cmd)
        self.assertIn("LocalPort 8700", ps)
        self.assertIn("control_center\\.web", ps)
        self.assertIn("service.service_cli stop", ps)
        self.assertNotIn("Stop-Process -Name", ps)

    def test_splash_reads_version_file(self):
        splash = (ROOT / "scripts" / "show_splash.ps1").read_text(encoding="utf-8-sig")
        self.assertIn('Join-Path $repoRoot "VERSION"', splash)
        self.assertIn('$version.Text = "V$displayVersion"', splash)
        self.assertNotIn('$version.Text = "V1.0"', splash)

if __name__ == "__main__":
    unittest.main()
