from __future__ import annotations

import unittest
from pathlib import Path

from assistant_deployment.manager import DeployPlan, _remote_script

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")


class V12oLocalAIDeployLifecycleContract(unittest.TestCase):
    def _plan(self):
        return DeployPlan(
            source=r"H:\EZStudioLab_assistant",
            source_commit="a" * 40,
            parent_gitlink_commit="a" * 40,
            node="steph@example",
            remote_root=r"C:\EZStudioLab_assistant",
            remote_host_repo=r"C:\EZStudioLab_assistant\runtime",
        )

    def test_local_ai_is_stopped_before_atomic_root_swap(self):
        rendered = _remote_script(self._plan(), "runtime.zip")
        self.assertLess(
            rendered.index("Stop-Process -Id $localAIPid"),
            rendered.index("[System.IO.Directory]::Move($remoteRoot, $previous)"),
        )
        self.assertIn("assistant_local_ai_stop_incomplete", rendered)

    def test_local_ai_manifest_drives_restart(self):
        rendered = _remote_script(self._plan(), "runtime.zip")
        self.assertIn(r"runtime\ai\cache-manifest.json", rendered)
        self.assertIn("EZSTUDIOLAB_LOCAL_AI_MODEL", rendered)
        self.assertIn("from app.local_ai_runtime import local_ai_start", rendered)

    def test_local_ai_health_is_checked_before_and_after_swap(self):
        rendered = _remote_script(self._plan(), "runtime.zip")
        self.assertGreaterEqual(rendered.count("http://127.0.0.1:8720/health"), 2)
        self.assertIn("assistant_local_ai_restart_health_timeout", rendered)

    def test_old_blocking_contract_is_removed(self):
        rendered = _remote_script(self._plan(), "runtime.zip")
        self.assertNotIn("assistant_local_ai_running_blocks_deploy", rendered)

    def test_rollback_stops_and_restarts_local_ai(self):
        self.assertIn("$rollbackAIWasRunning = $false", DEPLOY)
        self.assertIn("assistant_rollback_local_ai_stop_incomplete", DEPLOY)
        self.assertIn("assistant_rollback_local_ai_restart_health_timeout", DEPLOY)

    def test_generated_reference_php_is_not_migrated(self):
        rendered = _remote_script(self._plan(), "runtime.zip")
        self.assertNotIn(r"config\reference.php", rendered)


if __name__ == "__main__":
    unittest.main()
