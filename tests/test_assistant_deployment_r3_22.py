from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANAGER = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")
WRAPPER = (ROOT / "scripts" / "deploy-assistant-node.ps1").read_text(encoding="utf-8-sig")


class AssistantDeploymentR322Contract(unittest.TestCase):
    def test_orchestrator_owns_deployment(self):
        self.assertIn("class DeployPlan", MANAGER)
        self.assertIn("def build_plan(", MANAGER)
        self.assertIn("def deploy(", MANAGER)
        self.assertIn("assistant_deployment.manager", WRAPPER)

    def test_source_is_lab_submodule(self):
        self.assertIn(r'H:\EZStudio_lab', MANAGER)
        self.assertIn("EZStudioLab_assistant", MANAGER)
        self.assertIn('["ls-tree", "HEAD", "EZStudioLab_assistant"]', MANAGER)
        self.assertIn("assistant_source_not_parent_pinned", MANAGER)

    def test_xps_is_deployment_target_not_dev_clone(self):
        self.assertIn(r'C:\EZStudioLab_assistant', MANAGER)
        self.assertIn(r'C:\EZStudioLab_assistant\runtime', MANAGER)
        self.assertIn('["git", "archive", "--format=zip"', MANAGER)
        self.assertIn('copied = subprocess.run(', MANAGER)
        self.assertIn('"scp",', MANAGER)
        self.assertIn('str(archive),', MANAGER)
        self.assertIn('timeout=120,', MANAGER)
        self.assertIn('"ssh",', MANAGER)
        self.assertNotIn("git clone", MANAGER)
        self.assertNotIn("git pull", MANAGER)

    def test_minimal_runtime_is_bundled(self):
        self.assertIn("RUNTIME_FILES = (", MANAGER)
        self.assertIn('Path("python/ezstudio/distributed/capabilities.py")', MANAGER)
        self.assertIn('Path("python/ezstudio/distributed/model_resolver.py")', MANAGER)
        self.assertIn('Path("python/ezstudio/distributed/worker_protocol.py")', MANAGER)
        self.assertIn("remote_staging_runtime_missing", MANAGER)
        self.assertIn("remote_runtime_missing_after_install", MANAGER)
        self.assertNotIn("remote_host_repo_python_missing", MANAGER)

    def test_atomic_install_and_rollback_slot(self):
        self.assertIn(".__new", MANAGER)
        self.assertIn(".__previous", MANAGER)
        self.assertIn("DEPLOYED_COMMIT.txt", MANAGER)

    def test_no_secret_or_scientific_execution(self):
        self.assertNotIn("EZSTUDIOLAB_ASSISTANT_TOKEN", MANAGER)
        self.assertNotIn("EZSTUDIO_ANALYSIS_WORKER_TOKEN", MANAGER)
        self.assertNotIn("distributed-probe", MANAGER)
        self.assertNotIn("distributed-watch", MANAGER)
        self.assertIn('"secrets_deployed": False', MANAGER)
        self.assertIn('"scientific_execution_started": False', MANAGER)


if __name__ == "__main__":
    unittest.main()
