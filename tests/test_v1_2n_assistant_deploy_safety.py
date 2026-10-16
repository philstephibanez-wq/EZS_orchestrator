from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from assistant_deployment.manager import DeployPlan, _remote_deployed_commit, _remote_script

ROOT = Path(__file__).resolve().parents[1]
DEPLOY = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")


class V12nAssistantDeploySafetyContract(unittest.TestCase):
    def _plan(self):
        return DeployPlan(
            source=r"H:\EZStudioLab_assistant",
            source_commit="a" * 40,
            parent_gitlink_commit="a" * 40,
            node="steph@example",
            remote_root=r"C:\EZStudioLab_assistant",
            remote_host_repo=r"C:\EZStudioLab_assistant\runtime",
        )

    def test_remote_invalid_git_is_not_reported_as_unreachable(self):
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=4,
            stdout="",
            stderr="fatal: not a git repository",
        )
        with patch("assistant_deployment.manager.subprocess.run", return_value=completed):
            reachable, commit, error = _remote_deployed_commit(self._plan())
        self.assertTrue(reachable)
        self.assertIsNone(commit)
        self.assertIn("remote_git_invalid", error or "")

    def test_status_distinguishes_reachable_remote_error(self):
        self.assertIn('elif error:\n        state = "ERROR"', DEPLOY)

    def test_root_swap_uses_directory_move(self):
        rendered = _remote_script(self._plan(), "runtime.zip")
        self.assertIn("[System.IO.Directory]::Move($remoteRoot, $previous)", rendered)
        self.assertIn("[System.IO.Directory]::Move($staging, $remoteRoot)", rendered)
        self.assertNotIn("Move-Item -LiteralPath $remoteRoot -Destination $previous", rendered)

    def test_local_ai_is_handled_before_root_swap(self):
        rendered = _remote_script(self._plan(), "runtime.zip")
        swap = rendered.index("[System.IO.Directory]::Move($remoteRoot, $previous)")
        guard = rendered.find("assistant_local_ai_running_blocks_deploy")
        stop = rendered.find("Stop-Process -Id $localAIPid")
        lifecycle_position = guard if guard >= 0 else stop
        self.assertGreaterEqual(lifecycle_position, 0)
        self.assertLess(lifecycle_position, swap)

    def test_persistent_runtime_assets_are_handled(self):
        for token in ("'state'", "'ai'", "'models-cache'"):
            self.assertIn(token, DEPLOY)
        self.assertIn("[System.IO.Directory]::Move($persistentSource, $persistentTarget)", DEPLOY)
        self.assertIn("[System.IO.Directory]::Move($candidatePersistent, $previousPersistent)", DEPLOY)


if __name__ == "__main__":
    unittest.main()
