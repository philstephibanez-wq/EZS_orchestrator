from __future__ import annotations

import unittest
from unittest.mock import patch

from config.loader import load_runtime_config
from contracts.target import Target
from server_manager.manager import ServerManager


class R37ServerLifecycleGuardTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_runtime_config()

    def test_stop_refuses_while_analysis_active(self):
        manager = ServerManager(self.config)
        with patch("server_manager.manager.analysis_execution_active", return_value=True):
            with self.assertRaisesRegex(RuntimeError, "analysis execution active"):
                manager.stop(Target.DEV)

    def test_restart_refuses_while_analysis_active(self):
        manager = ServerManager(self.config)
        with patch("server_manager.manager.analysis_execution_active", return_value=True):
            with self.assertRaisesRegex(RuntimeError, "analysis execution active"):
                manager.restart(Target.DEV, "dev")


if __name__ == "__main__":
    unittest.main()
