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
    analysis_python: Path
    analysis_entrypoint: Path
    gpu_slots: int
    dev_url: str
    prod_url: str


def load_runtime_config(path: Path | None = None) -> RuntimeConfig:
    if path is None:
        path = Path(__file__).resolve().parent / "runtime.json"

    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema") != "ezs.orchestrator.config.v2":
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

    slots = int(data["resources"]["gpu_slots"])
    if slots < 1:
        raise ValueError("gpu_slots must be >= 1")

    transport = data["transport"]
    return RuntimeConfig(
        orchestrator_root=Path(data["orchestrator_root"]),
        dev=server(Target.DEV),
        prod=server(Target.PROD),
        analysis_python=Path(data["analysis"]["python"]),
        analysis_entrypoint=Path(data["analysis"]["entrypoint"]),
        gpu_slots=slots,
        dev_url=str(transport["dev_url"]).rstrip("/"),
        prod_url=str(transport["prod_url"]).rstrip("/"),
    )
