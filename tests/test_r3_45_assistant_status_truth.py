from __future__ import annotations

import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from assistant_supervision.manager import AssistantSupervisor

ROOT = Path(__file__).resolve().parents[1]


class R345AssistantStatusTruthContract(unittest.TestCase):
    def test_status_probe_uses_stdin_transport(self):
        supervisor = AssistantSupervisor(node="steph@example")
        completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="OK\n", stderr="")
        with patch("assistant_supervision.manager.subprocess.run", return_value=completed) as run:
            result = supervisor._run_ps("Write-Output 'OK'", timeout=7)

        self.assertEqual(result.returncode, 0)
        args, kwargs = run.call_args
        command = args[0]
        self.assertIn("-Command", command)
        self.assertIn("-", command)
        self.assertNotIn("-EncodedCommand", command)
        self.assertEqual(kwargs["input"], "Write-Output 'OK'")
        self.assertEqual(kwargs["timeout"], 7)

    def test_worker_inventory_cannot_override_global_runtime_status(self):
        text = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8-sig")
        supervision = text.split("function renderAssistantSupervision(payload){", 1)[1].split(
            "async function refreshAssistantSupervision()", 1
        )[0]
        workers = text.split("function renderAssistantWorkers(payload){", 1)[1].split(
            "async function refresh", 1
        )[0]

        self.assertIn('txt("assistantState",label);', supervision)
        self.assertIn('dot($("assistantDot")', supervision)
        self.assertNotIn('txt("assistantState"', workers)
        self.assertNotIn('dot($("assistantDot")', workers)
        self.assertIn("worker(s) en ligne", workers)


if __name__ == "__main__":
    unittest.main()
