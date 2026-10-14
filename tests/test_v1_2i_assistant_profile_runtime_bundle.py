from __future__ import annotations

import unittest
from pathlib import Path

import assistant_deployment.manager as manager


class AssistantProfileRuntimeBundleV12iContract(unittest.TestCase):
    def test_profile_runtime_bundle_manifest_is_canonical(self):
        self.assertIn(Path("python/engine.py"), manager.RUNTIME_FILES)
        self.assertIn(Path("python/ezstudio/__init__.py"), manager.RUNTIME_FILES)
        self.assertIn(
            Path("python/ezstudio/pipeline/__init__.py"),
            manager.RUNTIME_FILES,
        )
        self.assertIn(
            Path("python/ezstudio/pipeline/profile"),
            manager.RUNTIME_DIRECTORIES,
        )
        self.assertIn(
            Path("python/ezstudio/runtime"),
            manager.RUNTIME_DIRECTORIES,
        )
        self.assertIn(Path("presets/profile"), manager.RUNTIME_DIRECTORIES)
        self.assertIn("__pycache__", manager.RUNTIME_EXCLUDED_PARTS)
        self.assertIn(".pyc", manager.RUNTIME_EXCLUDED_SUFFIXES)
        self.assertIn(".pyo", manager.RUNTIME_EXCLUDED_SUFFIXES)

    def test_deployment_blocks_dirty_lab_runtime_dependencies(self):
        source = Path(manager.__file__).read_text(encoding="utf-8")
        self.assertIn("lab_runtime_dependencies_not_clean", source)
        self.assertIn(
            '["status", "--porcelain", "--", *runtime_scope]',
            source,
        )

    def test_remote_install_validates_profile_runtime_files(self):
        source = Path(manager.__file__).read_text(encoding="utf-8")
        self.assertIn("remote_profile_runner_missing_after_install", source)
        self.assertIn("remote_profile_passt_worker_missing_after_install", source)
        self.assertIn("remote_profile_shared_engine_missing_after_install", source)
        self.assertIn("remote_profile_preset_missing_after_install", source)

    def test_bundle_copies_runtime_directories_without_python_cache(self):
        source = Path(manager.__file__).read_text(encoding="utf-8")
        self.assertIn("for relative_dir in RUNTIME_DIRECTORIES:", source)
        self.assertIn('source_dir.rglob("*")', source)
        self.assertIn("RUNTIME_EXCLUDED_PARTS", source)
        self.assertIn("RUNTIME_EXCLUDED_SUFFIXES", source)


if __name__ == "__main__":
    unittest.main()
