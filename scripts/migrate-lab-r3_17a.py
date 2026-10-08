from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"{path}: migration anchor absent")
    path.write_text(text.replace(old, new, 1), encoding="utf-8", newline="\n")


def patch_runtime() -> None:
    path = ROOT / "config" / "runtime.json"
    data = json.loads(path.read_text(encoding="utf-8"))

    if data.get("schema") not in {
        "ezs.orchestrator.config.v4",
        "ezs.orchestrator.config.v5",
    }:
        raise RuntimeError(f"unsupported runtime schema before LAB migration: {data.get('schema')!r}")

    # Non-regression snapshot: DEV / PROD values are not altered.
    before_dev = json.dumps(data["servers"]["dev"], sort_keys=True)
    before_prod = json.dumps(data["servers"]["prod"], sort_keys=True)
    before_dev_transport = data["transport"]["dev_backend_url"]
    before_prod_transport = data["transport"]["prod_backend_url"]

    data["schema"] = "ezs.orchestrator.config.v5"
    data["servers"]["lab"] = {
        "root": r"H:\EZStudio_lab",
        "backend_port": 8701,
        "public_port": 8701,
        "allowed_envs": ["dev"],
        "default_env": "dev",
        "analysis_python": r"H:\Python\pythoncore-3.14-64\python.exe",
        "web_php": r"H:\PHP\php-8.5-x64\php.exe",
    }
    data["transport"]["lab_backend_url"] = "http://127.0.0.1:8701"

    if json.dumps(data["servers"]["dev"], sort_keys=True) != before_dev:
        raise RuntimeError("DEV runtime configuration changed unexpectedly")
    if json.dumps(data["servers"]["prod"], sort_keys=True) != before_prod:
        raise RuntimeError("PROD runtime configuration changed unexpectedly")
    if data["transport"]["dev_backend_url"] != before_dev_transport:
        raise RuntimeError("DEV transport changed unexpectedly")
    if data["transport"]["prod_backend_url"] != before_prod_transport:
        raise RuntimeError("PROD transport changed unexpectedly")

    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def patch_target() -> None:
    replace_once(
        ROOT / "contracts" / "target.py",
        'class Target(str, Enum):\n    DEV = "dev"\n    PROD = "prod"\n',
        'class Target(str, Enum):\n    DEV = "dev"\n    PROD = "prod"\n    LAB = "lab"\n',
    )


def patch_loader() -> None:
    p = ROOT / "config" / "loader.py"

    replace_once(
        p,
        "    prod: ServerSpec\n"
        "    dev_analysis_python: Path\n"
        "    prod_analysis_python: Path\n",
        "    prod: ServerSpec\n"
        "    lab: ServerSpec | None\n"
        "    dev_analysis_python: Path\n"
        "    prod_analysis_python: Path\n"
        "    lab_analysis_python: Path | None\n",
    )
    replace_once(
        p,
        "    prod_backend_url: str\n"
        "    dev_web_php: Path | None\n"
        "    prod_web_php: Path | None\n",
        "    prod_backend_url: str\n"
        "    lab_backend_url: str | None\n"
        "    dev_web_php: Path | None\n"
        "    prod_web_php: Path | None\n"
        "    lab_web_php: Path | None\n",
    )

    replace_once(
        p,
        "    def web_php_for(self, target: Target) -> Path:\n"
        "        configured = self.dev_web_php if target is Target.DEV else self.prod_web_php\n"
        "        return configured if configured is not None else Path(\"php\")\n",
        "    def web_php_for(self, target: Target) -> Path:\n"
        "        if target is Target.DEV:\n"
        "            configured = self.dev_web_php\n"
        "        elif target is Target.PROD:\n"
        "            configured = self.prod_web_php\n"
        "        elif target is Target.LAB:\n"
        "            configured = self.lab_web_php\n"
        "        else:\n"
        "            raise ValueError(f\"Unsupported target: {target!r}\")\n"
        "        return configured if configured is not None else Path(\"php\")\n",
    )

    replace_once(
        p,
        "    def analysis_python_for(self, target: Target) -> Path:\n"
        "        return self.dev_analysis_python if target is Target.DEV else self.prod_analysis_python\n",
        "    def analysis_python_for(self, target: Target) -> Path:\n"
        "        if target is Target.DEV:\n"
        "            return self.dev_analysis_python\n"
        "        if target is Target.PROD:\n"
        "            return self.prod_analysis_python\n"
        "        if target is Target.LAB and self.lab_analysis_python is not None:\n"
        "            return self.lab_analysis_python\n"
        "        raise ValueError(f\"Analysis Python unavailable for target: {target!r}\")\n",
    )

    replace_once(
        p,
        "    def transport_url_for(self, target: Target) -> str:\n"
        "        return self.dev_backend_url if target is Target.DEV else self.prod_backend_url\n",
        "    def transport_url_for(self, target: Target) -> str:\n"
        "        if target is Target.DEV:\n"
        "            return self.dev_backend_url\n"
        "        if target is Target.PROD:\n"
        "            return self.prod_backend_url\n"
        "        if target is Target.LAB and self.lab_backend_url:\n"
        "            return self.lab_backend_url\n"
        "        raise ValueError(f\"Transport URL unavailable for target: {target!r}\")\n",
    )

    replace_once(
        p,
        '        "ezs.orchestrator.config.v4",\n'
        "    }:\n",
        '        "ezs.orchestrator.config.v4",\n'
        '        "ezs.orchestrator.config.v5",\n'
        "    }:\n",
    )

    replace_once(
        p,
        "    dev = server(Target.DEV)\n"
        "    prod = server(Target.PROD)\n",
        "    dev = server(Target.DEV)\n"
        "    prod = server(Target.PROD)\n"
        "    lab = server(Target.LAB) if schema == \"ezs.orchestrator.config.v5\" else None\n",
    )

    replace_once(
        p,
        "    prod_web_php = (\n"
        "        Path(data[\"servers\"][\"prod\"][\"web_php\"])\n"
        "        if data[\"servers\"][\"prod\"].get(\"web_php\")\n"
        "        else None\n"
        "    )\n",
        "    prod_web_php = (\n"
        "        Path(data[\"servers\"][\"prod\"][\"web_php\"])\n"
        "        if data[\"servers\"][\"prod\"].get(\"web_php\")\n"
        "        else None\n"
        "    )\n"
        "    lab_web_php = (\n"
        "        Path(data[\"servers\"][\"lab\"][\"web_php\"])\n"
        "        if schema == \"ezs.orchestrator.config.v5\" and data[\"servers\"][\"lab\"].get(\"web_php\")\n"
        "        else None\n"
        "    )\n",
    )

    replace_once(
        p,
        "    if schema in {\"ezs.orchestrator.config.v3\", \"ezs.orchestrator.config.v4\"}:\n"
        "        dev_python = Path(data[\"servers\"][\"dev\"][\"analysis_python\"])\n"
        "        prod_python = Path(data[\"servers\"][\"prod\"][\"analysis_python\"])\n"
        "    else:\n"
        "        prod_python = Path(analysis[\"python\"])\n"
        "        dev_python = dev.root / \".venv-py313\" / \"Scripts\" / \"python.exe\"\n",
        "    if schema in {\"ezs.orchestrator.config.v3\", \"ezs.orchestrator.config.v4\", \"ezs.orchestrator.config.v5\"}:\n"
        "        dev_python = Path(data[\"servers\"][\"dev\"][\"analysis_python\"])\n"
        "        prod_python = Path(data[\"servers\"][\"prod\"][\"analysis_python\"])\n"
        "        lab_python = (\n"
        "            Path(data[\"servers\"][\"lab\"][\"analysis_python\"])\n"
        "            if schema == \"ezs.orchestrator.config.v5\"\n"
        "            else None\n"
        "        )\n"
        "    else:\n"
        "        prod_python = Path(analysis[\"python\"])\n"
        "        dev_python = dev.root / \".venv-py313\" / \"Scripts\" / \"python.exe\"\n"
        "        lab_python = None\n",
    )

    replace_once(
        p,
        "    if schema == \"ezs.orchestrator.config.v4\":\n"
        "        dev_backend_url = str(transport[\"dev_backend_url\"]).rstrip(\"/\")\n"
        "        prod_backend_url = str(transport[\"prod_backend_url\"]).rstrip(\"/\")\n"
        "    else:\n",
        "    if schema in {\"ezs.orchestrator.config.v4\", \"ezs.orchestrator.config.v5\"}:\n"
        "        dev_backend_url = str(transport[\"dev_backend_url\"]).rstrip(\"/\")\n"
        "        prod_backend_url = str(transport[\"prod_backend_url\"]).rstrip(\"/\")\n"
        "        lab_backend_url = (\n"
        "            str(transport[\"lab_backend_url\"]).rstrip(\"/\")\n"
        "            if schema == \"ezs.orchestrator.config.v5\"\n"
        "            else None\n"
        "        )\n"
        "    else:\n",
    )

    replace_once(
        p,
        "        prod_backend_url = str(\n"
        "            transport.get(\"prod_backend_url\") or f\"http://127.0.0.1:{prod.backend_port}\"\n"
        "        ).rstrip(\"/\")\n",
        "        prod_backend_url = str(\n"
        "            transport.get(\"prod_backend_url\") or f\"http://127.0.0.1:{prod.backend_port}\"\n"
        "        ).rstrip(\"/\")\n"
        "        lab_backend_url = None\n",
    )

    replace_once(
        p,
        "        prod=prod,\n"
        "        dev_analysis_python=dev_python,\n"
        "        prod_analysis_python=prod_python,\n",
        "        prod=prod,\n"
        "        lab=lab,\n"
        "        dev_analysis_python=dev_python,\n"
        "        prod_analysis_python=prod_python,\n"
        "        lab_analysis_python=lab_python,\n",
    )

    replace_once(
        p,
        "        prod_backend_url=prod_backend_url,\n"
        "        dev_web_php=dev_web_php,\n"
        "        prod_web_php=prod_web_php,\n",
        "        prod_backend_url=prod_backend_url,\n"
        "        lab_backend_url=lab_backend_url,\n"
        "        dev_web_php=dev_web_php,\n"
        "        prod_web_php=prod_web_php,\n"
        "        lab_web_php=lab_web_php,\n",
    )


def patch_target_registry() -> None:
    p = ROOT / "transport" / "targets.py"
    replace_once(
        p,
        "        if target is Target.DEV:\n"
        "            root = self.config.dev.root\n"
        "            override = os.environ.get(\"EZS_DEV_ANALYSIS_TOKEN\")\n"
        "        else:\n"
        "            root = self.config.prod.root\n"
        "            override = os.environ.get(\"EZS_PROD_ANALYSIS_TOKEN\")\n"
        "\n"
        "        url = self.config.transport_url_for(target)\n"
        "\n"
        "        env = read_env_local(root)\n"
        "        token = override or env.get(\"ANALYSIS_WORKER_TOKEN\") or \"\"\n",
        "        if target is Target.DEV:\n"
        "            root = self.config.dev.root\n"
        "            override = os.environ.get(\"EZS_DEV_ANALYSIS_TOKEN\")\n"
        "            token_key = \"ANALYSIS_WORKER_TOKEN\"\n"
        "        elif target is Target.PROD:\n"
        "            root = self.config.prod.root\n"
        "            override = os.environ.get(\"EZS_PROD_ANALYSIS_TOKEN\")\n"
        "            token_key = \"ANALYSIS_WORKER_TOKEN\"\n"
        "        elif target is Target.LAB and self.config.lab is not None:\n"
        "            root = self.config.lab.root\n"
        "            override = os.environ.get(\"EZS_LAB_ANALYSIS_TOKEN\")\n"
        "            token_key = \"EZSTUDIO_ANALYSIS_WORKER_TOKEN\"\n"
        "        else:\n"
        "            raise ValueError(f\"Unsupported target endpoint: {target!r}\")\n"
        "\n"
        "        url = self.config.transport_url_for(target)\n"
        "\n"
        "        env = read_env_local(root)\n"
        "        token = override or env.get(token_key) or \"\"\n",
    )


def patch_planner() -> None:
    p = ROOT / "executor" / "planner.py"

    replace_once(
        p,
        "    def root_for(self, target: Target) -> Path:\n"
        "        return self.config.dev.root if target is Target.DEV else self.config.prod.root\n"
        "\n"
        "    def forbidden_root_for(self, target: Target) -> Path:\n"
        "        return self.config.prod.root if target is Target.DEV else self.config.dev.root\n",
        "    def root_for(self, target: Target) -> Path:\n"
        "        if target is Target.DEV:\n"
        "            return self.config.dev.root\n"
        "        if target is Target.PROD:\n"
        "            return self.config.prod.root\n"
        "        if target is Target.LAB and self.config.lab is not None:\n"
        "            return self.config.lab.root\n"
        "        raise ValueError(f\"Unsupported target root: {target!r}\")\n"
        "\n"
        "    def forbidden_roots_for(self, target: Target) -> tuple[Path, ...]:\n"
        "        roots = [self.config.dev.root, self.config.prod.root]\n"
        "        if self.config.lab is not None:\n"
        "            roots.append(self.config.lab.root)\n"
        "        owned = self.root_for(target)\n"
        "        return tuple(root for root in roots if self._resolved(root) != self._resolved(owned))\n",
    )

    replace_once(
        p,
        "    def validate_external_path(self, job: JobEnvelope, path: Path) -> None:\n"
        "        forbidden = self.forbidden_root_for(job.target)\n"
        "        if self._is_under(path, forbidden):\n"
        "            raise RuntimeError(\n"
        "                f\"Cross-root path forbidden for {job.target.value}: {path}\"\n"
        "            )\n",
        "    def validate_external_path(self, job: JobEnvelope, path: Path) -> None:\n"
        "        for forbidden in self.forbidden_roots_for(job.target):\n"
        "            if self._is_under(path, forbidden):\n"
        "                raise RuntimeError(\n"
        "                    f\"Cross-root path forbidden for {job.target.value}: {path}\"\n"
        "                )\n",
    )

    replace_once(
        p,
        "        forbidden = self.forbidden_root_for(target)\n"
        "\n"
        "        if self._is_under(python_path, forbidden):\n"
        "            raise RuntimeError(\n"
        "                f\"Cross-root analysis Python forbidden for {target.value}: \"\n"
        "                f\"{python_path}\"\n"
        "            )\n"
        "\n"
        "        if not self._is_under(python_path, root):\n"
        "            raise RuntimeError(\n"
        "                f\"Analysis Python must be owned by {target.value} checkout: \"\n"
        "                f\"{python_path}\"\n"
        "            )\n",
        "        for forbidden in self.forbidden_roots_for(target):\n"
        "            if self._is_under(python_path, forbidden):\n"
        "                raise RuntimeError(\n"
        "                    f\"Cross-root analysis Python forbidden for {target.value}: \"\n"
        "                    f\"{python_path}\"\n"
        "                )\n"
        "\n"
        "        if target is Target.LAB:\n"
        "            configured = self.config.lab_analysis_python\n"
        "            if configured is None or self._resolved(python_path) != self._resolved(configured):\n"
        "                raise RuntimeError(\n"
        "                    f\"LAB analysis Python must match configured executable: {python_path}\"\n"
        "                )\n"
        "            return\n"
        "\n"
        "        if not self._is_under(python_path, root):\n"
        "            raise RuntimeError(\n"
        "                f\"Analysis Python must be owned by {target.value} checkout: \"\n"
        "                f\"{python_path}\"\n"
        "            )\n",
    )


def patch_capability() -> None:
    replace_once(
        ROOT / "capability" / "publisher.py",
        "    def _root_for(self, target: Target) -> Path:\n"
        "        return self.config.dev.root if target is Target.DEV else self.config.prod.root\n",
        "    def _root_for(self, target: Target) -> Path:\n"
        "        if target is Target.DEV:\n"
        "            return self.config.dev.root\n"
        "        if target is Target.PROD:\n"
        "            return self.config.prod.root\n"
        "        if target is Target.LAB and self.config.lab is not None:\n"
        "            return self.config.lab.root\n"
        "        raise ValueError(f\"Unsupported capability target: {target!r}\")\n",
    )


def patch_service() -> None:
    p = ROOT / "service" / "runner.py"
    replace_once(
        p,
        "def targets_for_scope(target: Target | None) -> tuple[Target, ...]:\n"
        "    return (Target.DEV, Target.PROD) if target is None else (target,)\n",
        "def targets_for_scope(target: Target | None) -> tuple[Target, ...]:\n"
        "    return (Target.DEV, Target.PROD, Target.LAB) if target is None else (target,)\n",
    )
    replace_once(
        p,
        "    target=None means the single machine-wide service serves DEV and PROD.\n",
        "    target=None means the single machine-wide service serves DEV, PROD and LAB.\n",
    )

    p = ROOT / "service" / "service_cli.py"
    replace_once(
        p,
        '            "--target", choices=("all", "dev", "prod"), required=True,\n'
        '            help="all = one permanent service polling DEV and PROD",\n',
        '            "--target", choices=("all", "dev", "prod", "lab"), required=True,\n'
        '            help="all = one permanent service polling DEV, PROD and LAB",\n',
    )


def patch_cli() -> None:
    p = ROOT / "control_center" / "cli.py"
    replace_once(
        p,
        "    targets = (target,) if target is not None else (Target.DEV, Target.PROD)\n",
        "    targets = (target,) if target is not None else (Target.DEV, Target.PROD, Target.LAB)\n",
    )
    replace_once(
        p,
        '    queue_parser.add_argument("--target", choices=("dev", "prod"), default=None)\n',
        '    queue_parser.add_argument("--target", choices=("dev", "prod", "lab"), default=None)\n',
    )
    replace_once(
        p,
        '    run_parser.add_argument("--target", choices=("dev", "prod"), required=True)\n',
        '    run_parser.add_argument("--target", choices=("dev", "prod", "lab"), required=True)\n',
    )
    # Server lifecycle deliberately remains dev/prod only.


def patch_history() -> None:
    replace_once(
        ROOT / "control_center" / "job_history.py",
        '        for target in ("dev", "prod"):\n',
        '        for target in ("dev", "prod", "lab"):\n',
    )


def patch_existing_contract_test() -> None:
    p = ROOT / "tests" / "test_r3_11_analysis_capability.py"
    replace_once(
        p,
        "    def test_all_scope_contains_both_targets(self):\n"
        "        self.assertEqual(\n"
        "            targets_for_scope(None),\n"
        "            (Target.DEV, Target.PROD),\n"
        "        )\n"
        "        self.assertEqual(targets_for_scope(Target.DEV), (Target.DEV,))\n"
        "        self.assertEqual(targets_for_scope(Target.PROD), (Target.PROD,))\n",
        "    def test_all_scope_contains_all_targets(self):\n"
        "        self.assertEqual(\n"
        "            targets_for_scope(None),\n"
        "            (Target.DEV, Target.PROD, Target.LAB),\n"
        "        )\n"
        "        self.assertEqual(targets_for_scope(Target.DEV), (Target.DEV,))\n"
        "        self.assertEqual(targets_for_scope(Target.PROD), (Target.PROD,))\n"
        "        self.assertEqual(targets_for_scope(Target.LAB), (Target.LAB,))\n",
    )


def main() -> int:
    patch_runtime()
    patch_target()
    patch_loader()
    patch_target_registry()
    patch_planner()
    patch_capability()
    patch_service()
    patch_cli()
    patch_history()
    patch_existing_contract_test()

    print("EZS_ORCHESTRATOR_LAB_R3_17A_MIGRATION_OK")
    print("EZS_ORCHESTRATOR_DEV_PROD_RUNTIME_UNCHANGED_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
