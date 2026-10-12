from __future__ import annotations

import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"

FORBIDDEN_SCRIPT_PATTERNS = (
    re.compile(r"^apply[-_].*", re.I),
    re.compile(r"^migrate[-_].*", re.I),
    re.compile(r"^preflight[-_].*", re.I),
    re.compile(r".*hotfix.*", re.I),
    re.compile(r"^rollback[-_].*", re.I),
    re.compile(r"^cleanup[-_].*", re.I),
    re.compile(r"^status[-_].*r\d", re.I),
)

ALLOWED_DURABLE_SCRIPTS = {
    "deploy-assistant-node.ps1",
    "launch_hidden.ps1",
    "show_splash.ps1",
    "start_control_center.ps1",
}


def tracked_files() -> set[str]:
    completed = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return {line.strip().replace("\\", "/") for line in completed.stdout.splitlines() if line.strip()}


class RepositoryHygieneContract(unittest.TestCase):
    def test_scripts_directory_contains_only_durable_product_scripts(self):
        files = {p.name for p in SCRIPTS.iterdir() if p.is_file()}
        offenders = sorted(
            name for name in files
            if any(pattern.match(name) for pattern in FORBIDDEN_SCRIPT_PATTERNS)
        )
        self.assertEqual([], offenders, f"Temporary/one-shot scripts must live in H:\\temp: {offenders}")
        self.assertEqual(ALLOWED_DURABLE_SCRIPTS, files)

    def test_no_tracked_delivery_archives_or_backups(self):
        offenders = []
        for relative in tracked_files():
            name = Path(relative).name.lower()
            if (
                name.endswith(".zip")
                or ".before_" in name
                or name.endswith(".bak")
                or name.endswith(".tmp")
            ):
                offenders.append(relative)
        self.assertEqual([], sorted(offenders))


if __name__ == "__main__":
    unittest.main()
