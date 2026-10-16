from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")

class R342AssistantDeploymentVersionHelpersContract(unittest.TestCase):
    def test_version_helpers_preserved(self):
        self.assertIn("def _version_from_file(path: Path) -> str | None:", SOURCE)
        self.assertIn("def _source_version(plan: DeployPlan) -> str | None:", SOURCE)
        self.assertIn('return _version_from_file(Path(plan.source) / "VERSION")', SOURCE)

    def test_runtime_fingerprint_addition_does_not_replace_version_helpers(self):
        self.assertIn("def _runtime_fingerprint() -> str:", SOURCE)
        self.assertIn("source_version = _source_version(plan)", SOURCE)

if __name__ == "__main__":
    unittest.main()
