from __future__ import annotations

import inspect
import unittest

import assistant_deployment.manager as manager


class AssistantInstallerTransportV12jContract(unittest.TestCase):
    def test_remote_installer_is_transferred_as_ps1(self):
        source = inspect.getsource(manager.deploy)
        self.assertIn("remote_script_name =", source)
        self.assertIn("remote_script_path.write_text(", source)
        self.assertIn('"utf-8-sig"', source)
        self.assertIn("str(remote_script_path)", source)
        self.assertIn('f"{plan.node}:."', source)

    def test_installation_uses_powershell_file_not_encoded_command(self):
        source = inspect.getsource(manager.deploy)
        self.assertIn('"-File"', source)
        self.assertNotIn('"EncodedCommand"', source)
        self.assertNotIn("base64.b64encode(remote.encode", source)

    def test_existing_remote_script_and_atomic_install_remain_canonical(self):
        source = inspect.getsource(manager._remote_script)
        self.assertIn(".__new", source)
        self.assertIn(".__previous", source)
        self.assertIn("remote_commit_mismatch", source)
        self.assertIn("remote_profile_runner_missing_after_install", source)
        self.assertIn("remote_profile_passt_worker_missing_after_install", source)
        self.assertIn("remote_profile_shared_engine_missing_after_install", source)
        self.assertIn("remote_profile_preset_missing_after_install", source)

    def test_remote_temp_cleanup_is_bounded(self):
        source = inspect.getsource(manager.deploy)
        self.assertIn("cleanup_command =", source)
        self.assertIn("remote_script_name", source)
        self.assertIn("remote_archive_name", source)
        self.assertIn('"-Command"', source)


if __name__ == "__main__":
    unittest.main()
