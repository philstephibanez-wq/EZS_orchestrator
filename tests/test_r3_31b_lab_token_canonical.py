from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from contracts.target import Target
from transport.targets import TargetRegistry


class _Config:
    def __init__(self, root: Path):
        self.dev = SimpleNamespace(root=root / "dev")
        self.prod = SimpleNamespace(root=root / "prod")
        self.lab = SimpleNamespace(root=root / "lab")
        for item in (self.dev, self.prod, self.lab):
            item.root.mkdir(parents=True, exist_ok=True)

    def transport_url_for(self, target: Target) -> str:
        return f"http://127.0.0.1/{target.value}"


class R331BLabTokenCanonicalContract(unittest.TestCase):
    def test_lab_env_local_beats_stale_inherited_override(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = _Config(Path(tmp))
            (config.lab.root / ".env.local").write_text(
                "EZSTUDIO_ANALYSIS_WORKER_TOKEN=canonical-lab-token\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"EZS_LAB_ANALYSIS_TOKEN": "stale-inherited-token"},
                clear=False,
            ):
                endpoint = TargetRegistry(config).endpoint(Target.LAB)

            self.assertEqual(endpoint.token, "canonical-lab-token")

    def test_lab_override_is_fallback_when_env_local_has_no_token(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = _Config(Path(tmp))
            (config.lab.root / ".env.local").write_text(
                "OTHER_KEY=value\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"EZS_LAB_ANALYSIS_TOKEN": "fallback-lab-token"},
                clear=False,
            ):
                endpoint = TargetRegistry(config).endpoint(Target.LAB)

            self.assertEqual(endpoint.token, "fallback-lab-token")

    def test_dev_override_semantics_are_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = _Config(Path(tmp))
            (config.dev.root / ".env.local").write_text(
                "ANALYSIS_WORKER_TOKEN=dev-file-token\n",
                encoding="utf-8",
            )
            with patch.dict(
                os.environ,
                {"EZS_DEV_ANALYSIS_TOKEN": "dev-override-token"},
                clear=False,
            ):
                endpoint = TargetRegistry(config).endpoint(Target.DEV)

            self.assertEqual(endpoint.token, "dev-override-token")


if __name__ == "__main__":
    unittest.main()
