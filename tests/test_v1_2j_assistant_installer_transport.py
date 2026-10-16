from __future__ import annotations

import inspect
import unittest

import assistant_deployment.manager as manager


class AssistantInstallerTransportV12jContract(unittest.TestCase):
    def test_runtime_bundle_is_transferred_separately(self):
        source = inspect.getsource(manager.deploy)
        self.assertIn("runtime-", source)
        self.assertIn("str(archive)", source)
        self.assertIn("remote_script_path", source)

    def test_application_deploy_is_clean_git_clone(self):
        source = inspect.getsource(manager._remote_script)
        self.assertIn("git clone --branch main --single-branch", source)
        self.assertIn("git -C $staging rev-parse HEAD", source)
        self.assertIn("git -C $remoteRoot status --porcelain", source)

    def test_composer_runs_only_when_vendor_cannot_be_reused(self):
        source = inspect.getsource(manager._remote_script)
        self.assertIn("COMPOSER_LOCK_IDENTICAL reuse_vendor", source)
        self.assertIn("composer install --no-interaction --prefer-dist --no-progress", source)
        self.assertIn("if ($reuseVendor)", source)

    def test_runtime_is_external_to_clone(self):
        self.assertEqual(
            r"C:\EZStudioLab_assistant\runtime",
            manager.DEFAULT_REMOTE_HOST_REPO,
        )


if __name__ == "__main__":
    unittest.main()
