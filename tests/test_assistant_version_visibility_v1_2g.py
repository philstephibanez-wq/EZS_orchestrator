from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from assistant_deployment.manager import (
    DeployPlan,
    build_status_plan,
    deployment_status,
)


class AssistantVersionVisibilityContract(unittest.TestCase):
    def _plan(self, source: str) -> DeployPlan:
        return DeployPlan(
            source=source,
            source_commit="a" * 40,
            parent_gitlink_commit="a" * 40,
            node="test@example",
            remote_root=r"C:\\EZStudioLab_assistant",
            remote_host_repo=r"C:\\EZStudioLab_assistant\\runtime",
        )

    def test_status_exposes_human_versions_and_keeps_builds(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "VERSION").write_text(
                "1.2g\n",
                encoding="utf-8",
            )
            plan = self._plan(tmp)

            with patch(
                "assistant_deployment.manager._git",
                return_value="",
            ), patch(
                "assistant_deployment.manager._remote_deployed_commit",
                return_value=(True, "a" * 40, None),
            ), patch(
                "assistant_deployment.manager._remote_deployed_version",
                return_value=(True, "1.2g", None),
            ):
                status = deployment_status(plan)

        self.assertEqual(status["state"], "UP_TO_DATE")
        self.assertEqual(status["source_version"], "1.2g")
        self.assertEqual(status["deployed_version"], "1.2g")
        self.assertEqual(status["source_commit"], "a" * 40)
        self.assertEqual(status["deployed_commit"], "a" * 40)

    def test_dirty_source_is_visible_without_blocking_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "VERSION").write_text(
                "1.2d\n",
                encoding="utf-8",
            )
            plan = self._plan(tmp)

            with patch(
                "assistant_deployment.manager._git",
                return_value=" M VERSION",
            ), patch(
                "assistant_deployment.manager._remote_deployed_commit",
                return_value=(True, "a" * 40, None),
            ), patch(
                "assistant_deployment.manager._remote_deployed_version",
                return_value=(True, "1.2c", None),
            ):
                status = deployment_status(plan)

        self.assertEqual(status["state"], "LOCAL_CHANGES")
        self.assertEqual(status["source_version"], "1.2d")
        self.assertEqual(status["deployed_version"], "1.2c")
        self.assertTrue(status["source_dirty"])

    def test_update_state_stays_commit_based(self):
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "VERSION").write_text(
                "1.2g\n",
                encoding="utf-8",
            )
            plan = self._plan(tmp)

            with patch(
                "assistant_deployment.manager._git",
                return_value="",
            ), patch(
                "assistant_deployment.manager._remote_deployed_commit",
                return_value=(True, "b" * 40, None),
            ), patch(
                "assistant_deployment.manager._remote_deployed_version",
                return_value=(True, "1.2f", None),
            ):
                status = deployment_status(plan)

        self.assertEqual(status["state"], "UPDATE_AVAILABLE")
        self.assertEqual(status["source_version"], "1.2g")
        self.assertEqual(status["deployed_version"], "1.2f")


class WebContract(unittest.TestCase):
    def test_human_versions_are_primary_and_git_builds_secondary(self):
        web = Path("control_center/web.py").read_text(encoding="utf-8")

        self.assertIn(
            '<dt>Version source</dt><dd id="assistantSourceVersion">-</dd>',
            web,
        )
        self.assertIn(
            '<dt>Version déployée</dt><dd id="assistantDeployedVersion">-</dd>',
            web,
        )
        self.assertIn("Détails techniques Git", web)
        self.assertIn("MODIFICATIONS LOCALES", web)
        self.assertIn("build_assistant_status_plan()", web)
        self.assertIn('txt("assistantSourceVersion",', web)
        self.assertIn('txt("assistantDeployedVersion",', web)
        self.assertIn('txt("assistantSourceCommit",', web)
        self.assertIn('txt("assistantDeployedCommit",', web)


if __name__ == "__main__":
    unittest.main()
