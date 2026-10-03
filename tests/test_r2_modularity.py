from __future__ import annotations

import ast
import unittest
from pathlib import Path

from config.loader import load_runtime_config
from contracts.job import JobEnvelope
from contracts.target import Target
from executor.planner import ExecutionPlanner
from server_manager.manager import ServerManager


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    found: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                found.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                found.add(node.module)

    return found


class R2ModularityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = Path(__file__).resolve().parents[1]
        cls.config = load_runtime_config()

    def test_prod_is_prod_only(self):
        manager = ServerManager(self.config)
        manager.spec(Target.PROD).validate_env("prod")
        with self.assertRaises(ValueError):
            manager.spec(Target.PROD).validate_env("dev")

    def test_dev_allows_prod_mode_without_changing_root(self):
        manager = ServerManager(self.config)
        spec = manager.spec(Target.DEV)
        self.assertEqual(spec.validate_env("prod"), "prod")
        self.assertEqual(spec.root, Path(r"H:\EZScore_dev"))

    def test_executor_follows_checkout(self):
        planner = ExecutionPlanner(self.config)
        dev = planner.plan(JobEnvelope(1, Target.DEV, "lyrics"))
        prod = planner.plan(JobEnvelope(2, Target.PROD, "lyrics"))
        self.assertEqual(dev.project_root, Path(r"H:\EZScore_dev"))
        self.assertEqual(prod.project_root, Path(r"H:\EZScore"))

    def test_recursive_cross_root_guard(self):
        planner = ExecutionPlanner(self.config)
        job = JobEnvelope(
            3,
            Target.DEV,
            "stems",
            payload={"paths": {"source": r"H:\EZScore\var\storage\bad.wav"}},
        )
        with self.assertRaises(RuntimeError):
            planner.plan(job)

    def test_server_manager_has_no_scheduler_or_analysis_imports(self):
        modules = imported_modules(self.root / "server_manager" / "manager.py")
        forbidden_prefixes = (
            "scheduler",
            "executor",
            "transport",
            "worker_app",
            "analysis",
        )
        for module in modules:
            self.assertFalse(
                module.startswith(forbidden_prefixes),
                f"server_manager imports forbidden module: {module}",
            )

    def test_scheduler_has_no_transport_or_analysis_imports(self):
        modules = imported_modules(self.root / "scheduler" / "scheduler.py")
        forbidden_prefixes = (
            "transport",
            "executor",
            "server_manager",
            "worker_app",
            "analysis",
        )
        for module in modules:
            self.assertFalse(
                module.startswith(forbidden_prefixes),
                f"scheduler imports forbidden module: {module}",
            )


if __name__ == "__main__":
    unittest.main()
