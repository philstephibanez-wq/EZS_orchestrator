from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from contracts.server import ServerSpec
from contracts.target import Target


@dataclass(frozen=True, slots=True)
class RuntimeConfig:
    orchestrator_root: Path
    dev: ServerSpec
    prod: ServerSpec
    dev_analysis_python: Path
    prod_analysis_python: Path
    analysis_entrypoint: Path
    gpu_slots: int
    dev_backend_url: str
    prod_backend_url: str
    dev_web_php: Path | None
    prod_web_php: Path | None

    def web_php_for(self, target: Target) -> Path:
        configured = self.dev_web_php if target is Target.DEV else self.prod_web_php
        return configured if configured is not None else Path("php")

    def analysis_python_for(self, target: Target) -> Path:
        return self.dev_analysis_python if target is Target.DEV else self.prod_analysis_python

    def transport_url_for(self, target: Target) -> str:
        return self.dev_backend_url if target is Target.DEV else self.prod_backend_url

    @property
    def analysis_python(self) -> Path:
        return self.prod_analysis_python

    @property
    def dev_url(self) -> str:
        return self.dev_backend_url

    @property
    def prod_url(self) -> str:
        return self.prod_backend_url


def load_runtime_config(path: Path | None = None) -> RuntimeConfig:
    if path is None:
        path = Path(__file__).resolve().parent / "runtime.json"

    data = json.loads(path.read_text(encoding="utf-8"))
    schema = data.get("schema")
    if schema not in {
        "ezs.orchestrator.config.v2",
        "ezs.orchestrator.config.v3",
        "ezs.orchestrator.config.v4",
    }:
        raise ValueError("Unsupported orchestrator config schema")

    def server(target: Target) -> ServerSpec:
        raw = data["servers"][target.value]
        return ServerSpec(
            target=target,
            root=Path(raw["root"]),
            backend_port=int(raw["backend_port"]),
            public_port=int(raw["public_port"]),
            gateway_port=int(raw["gateway_port"]) if raw.get("gateway_port") else None,
            allowed_envs=tuple(raw["allowed_envs"]),
            default_env=str(raw["default_env"]),
        )

    dev = server(Target.DEV)
    prod = server(Target.PROD)

    dev_web_php = (
        Path(data["servers"]["dev"]["web_php"])
        if data["servers"]["dev"].get("web_php")
        else None
    )
    prod_web_php = (
        Path(data["servers"]["prod"]["web_php"])
        if data["servers"]["prod"].get("web_php")
        else None
    )

    slots = int(data["resources"]["gpu_slots"])
    if slots < 1:
        raise ValueError("gpu_slots must be >= 1")

    analysis = data["analysis"]

    if schema in {"ezs.orchestrator.config.v3", "ezs.orchestrator.config.v4"}:
        dev_python = Path(data["servers"]["dev"]["analysis_python"])
        prod_python = Path(data["servers"]["prod"]["analysis_python"])
    else:
        prod_python = Path(analysis["python"])
        dev_python = dev.root / ".venv-py313" / "Scripts" / "python.exe"

    transport = data.get("transport") or {}
    if schema == "ezs.orchestrator.config.v4":
        dev_backend_url = str(transport["dev_backend_url"]).rstrip("/")
        prod_backend_url = str(transport["prod_backend_url"]).rstrip("/")
    else:
        dev_backend_url = str(
            transport.get("dev_backend_url") or f"http://127.0.0.1:{dev.backend_port}"
        ).rstrip("/")
        prod_backend_url = str(
            transport.get("prod_backend_url") or f"http://127.0.0.1:{prod.backend_port}"
        ).rstrip("/")

    return RuntimeConfig(
        orchestrator_root=Path(data["orchestrator_root"]),
        dev=dev,
        prod=prod,
        dev_analysis_python=dev_python,
        prod_analysis_python=prod_python,
        analysis_entrypoint=Path(analysis["entrypoint"]),
        gpu_slots=slots,
        dev_backend_url=dev_backend_url,
        prod_backend_url=prod_backend_url,
        dev_web_php=dev_web_php,
        prod_web_php=prod_web_php,
    )
