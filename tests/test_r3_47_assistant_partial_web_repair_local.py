from __future__ import annotations

import subprocess
import unittest
from unittest.mock import MagicMock, patch

from assistant_supervision.manager import AssistantSupervisor


class R347AssistantPartialWebRepairLocalContract(unittest.TestCase):
    def test_start_repairs_partial_web_before_remote_helper(self):
        supervisor = AssistantSupervisor(node="steph@example")
        supervisor._configured_token = MagicMock(return_value="token")
        supervisor._repair_partial_web = MagicMock()
        supervisor._run_remote_helper = MagicMock(
            return_value=subprocess.CompletedProcess(
                args=[], returncode=0, stdout="OK", stderr=""
            )
        )
        supervisor.status = MagicMock(
            return_value={
                "state": "RUNNING",
                "process_count": 1,
                "profile_review_count": 1,
                "web_running": True,
                "web_listener_count": 2,
                "web_version": "1.3i",
                "deployed_commit": "abc",
            }
        )
        result = supervisor.start()
        supervisor._repair_partial_web.assert_called_once_with()
        supervisor._run_remote_helper.assert_called_once()
        self.assertEqual(result["state"], "RUNNING")

    def test_partial_web_repair_uses_web_stop_only(self):
        supervisor = AssistantSupervisor(node="steph@example")
        completed = subprocess.CompletedProcess(
            args=[], returncode=0, stdout="OK", stderr=""
        )
        with patch.object(supervisor, "_run_ps", return_value=completed) as run_ps:
            supervisor._repair_partial_web()
        script = run_ps.call_args.args[0]
        self.assertIn("scripts\\stop.cmd", script)
        self.assertIn("$has8712 -xor $has8713", script)
        self.assertNotIn("assistant-supervision.ps1", script)
        self.assertNotIn("distributed-watch", script)
        self.assertNotIn("profile-review-auto-watch", script)


if __name__ == "__main__":
    unittest.main()
