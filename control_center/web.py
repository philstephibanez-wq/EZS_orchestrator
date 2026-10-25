from __future__ import annotations

import argparse
import json
import os
import secrets
import sqlite3
import subprocess
import sys
import threading
import time
import webbrowser
import urllib.error
import urllib.request
from dataclasses import asdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from caddy_manager.manager import CaddyManager
from config.loader import load_runtime_config
from contracts.target import Target
from control_center.incidents import IncidentStore
from control_center.job_history import JobHistory
from control_center.log_tools import LogTools
from control_center.singleton import ControlCenterSingleton, ControlCenterSingletonBusy
from deployment.manager import DeploymentManager
from assistant_deployment.manager import build_plan as build_assistant_deploy_plan, build_status_plan as build_assistant_status_plan, deploy as deploy_assistant_node, deployment_status as get_assistant_deployment_status, finalize_deployment as finalize_assistant_deployment, rollback_deployment as rollback_assistant_deployment
from assistant_supervision.manager import AssistantSupervisor
from gateway_manager.manager import GatewayManager
from prod_lifecycle.manager import ProdLifecycleManager
from runtime_guard.activity import analysis_execution_active
from server_manager.manager import ServerManager
from server_manager.process import clear_process_cache, command_line, executable_path, pid_alive, process_metrics
from service.lab_circuit import LabCircuitBreaker
from transport.jobs import JobTransport
from transport.targets import TargetRegistry

HOST = "127.0.0.1"
DEFAULT_PORT = 8700
SNAPSHOT_CACHE_SECONDS = 1.0


def _read_version(path: Path) -> str:
    try:
        value = path.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return "-"
    return value or "-"


VERSION = _read_version(Path(__file__).resolve().parents[1] / "VERSION")
DEV_VERSION = _read_version(Path(r"H:\EZScore_dev") / "VERSION")
LAB_VERSION = _read_version(Path(r"H:\EZStudio_lab") / "VERSION")
ASSISTANT_VERSION = _read_version(
    Path(r"H:\EZStudioLab_assistant") / "VERSION"
)


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


class ControlCenter:
    def __init__(self) -> None:
        self.config = load_runtime_config()
        self.servers = ServerManager(self.config)
        self.caddy = CaddyManager(self.config)
        self.gateway = GatewayManager(self.config)
        self.prod = ProdLifecycleManager(
            self.config,
            servers=self.servers,
            gateway=self.gateway,
            caddy=self.caddy,
        )
        self.transport = JobTransport(TargetRegistry(self.config))
        self.log_tools = LogTools(self.config.orchestrator_root)
        self.incidents = IncidentStore(self.config.orchestrator_root / "runtime")
        self.lab_circuit = LabCircuitBreaker(self.config.orchestrator_root / "runtime")
        self.job_history = JobHistory(self.config.orchestrator_root)
        self.deployment = DeploymentManager(self.config, self.prod)
        self.assistant_supervision = AssistantSupervisor()
        self.action_lock = threading.Lock()
        self.snapshot_lock = threading.Lock()
        self._snapshot_cache: dict | None = None
        self._snapshot_cache_at = 0.0

    @property
    def runtime(self) -> Path:
        return self.config.orchestrator_root / "runtime"

    def _service_status(self) -> dict:
        service_dir = self.runtime / "service"
        meta_path = service_dir / "service.json"
        stop_path = service_dir / "stop.request"
        meta = _read_json(meta_path)
        heartbeat = _read_json(service_dir / "heartbeat.json")
        if not meta:
            return {
                "running": False,
                "pid": None,
                "target": None,
                "poll_seconds": None,
                "state": "stopped",
                "heartbeat": heartbeat.get("at"),
            }
        try:
            pid = int(meta.get("pid") or 0)
        except Exception:
            pid = 0
        clear_process_cache()
        if pid <= 0 or not pid_alive(pid):
            meta_path.unlink(missing_ok=True)
            stop_path.unlink(missing_ok=True)
            return {
                "running": False,
                "pid": None,
                "target": None,
                "poll_seconds": None,
                "state": "stopped",
                "heartbeat": heartbeat.get("at"),
            }
        exe = executable_path(pid)
        cmd = command_line(pid)
        expected = False
        if exe and cmd:
            try:
                expected = (
                    Path(exe).resolve()
                    == Path(sys.executable).resolve()
                    and "-m service.service_cli run"
                    in cmd.lower()
                )
            except Exception:
                expected = False
        metrics = process_metrics(pid)
        return {
            "running": True,
            "pid": pid,
            "target": meta.get("target"),
            "poll_seconds": meta.get("poll_seconds"),
            "state": heartbeat.get("state", "unknown"),
            "heartbeat": heartbeat.get("at"),
            "ownership": "owned" if expected else "foreign",
            "executable_path": exe,
            "command_line": cmd,
            "cpu_percent": metrics.get("cpu_percent"),
            "ram_mb": metrics.get("ram_mb"),
        }

    def _queue(self, target: Target) -> dict:
        try:
            jobs = self.transport.queue(target)
            return {"ok": True, "count": len(jobs), "jobs": jobs[:50]}
        except Exception as exc:
            return {"ok": False, "count": None, "jobs": [], "error": str(exc)}

    def _distributed_workers(self) -> dict:
        try:
            workers = self.transport.distributed_workers(Target.LAB)
            return {"ok": True, "count": len(workers), "workers": workers}
        except Exception as exc:
            return {
                "ok": False,
                "count": None,
                "workers": [],
                "error": f"{type(exc).__name__}:{exc}"[:500],
            }
    @staticmethod
    def _heartbeat_age_seconds(value: object) -> float | None:
        raw = str(value or "").strip()
        if not raw:
            return None
        try:
            stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if stamp.tzinfo is None:
                stamp = stamp.replace(tzinfo=timezone.utc)
            return max(0.0, (datetime.now(timezone.utc) - stamp).total_seconds())
        except Exception:
            return None

    @staticmethod
    def _log_key_for_source(source: str) -> str:
        mapping = {
            "logs/control-center-error.log": "control_center_error",
            "runtime/service/service.err.log": "service_error",
            "logs/servers/dev.err.log": "dev_server_error",
            "logs/servers/prod.err.log": "prod_server_error",
            "logs/servers/lab.err.log": "lab_server_error",
            "logs/gateway/prod.err.log": "prod_gateway_error",
            "runtime/caddy/dev/caddy.err.log": "dev_caddy_error",
            "runtime/caddy/prod/caddy.err.log": "prod_caddy_error",
            "runtime/caddy/lab/caddy.err.log": "lab_caddy_error",
        }
        return mapping.get(source, "control_center_error")

    def _safety_status(self, snapshot: dict) -> dict:
        issues: list[dict] = []
        service = snapshot.get("service") or {}
        if (
            service.get("running")
            and service.get("ownership") == "foreign"
        ):
            issues.append({
                "severity": "critical",
                "code": "foreign_process",
                "source": "service",
                "message": (
                    "Service permanent: identité processus "
                    f"inattendue (pid={service.get('pid')})."
                ),
                "log_key": "service_error",
            })
        if service.get("running"):
            age = self._heartbeat_age_seconds(
                service.get("heartbeat")
            )
            if age is None or age > 15.0:
                issues.append({
                    "severity": "error",
                    "code": "heartbeat_stale",
                    "source": "service",
                    "message": (
                        "Service permanent sans heartbeat récent "
                        f"({age if age is not None else 'inconnu'} s)."
                    ),
                    "log_key": "service_error",
                })

        rows = (
            (
                "DEV serveur",
                ((snapshot.get("dev") or {}).get("server") or {}),
                "dev_server_error",
            ),
            (
                "DEV Caddy",
                ((snapshot.get("dev") or {}).get("caddy") or {}),
                "dev_caddy_error",
            ),
            (
                "PROD serveur",
                (
                    (((snapshot.get("prod") or {}).get(
                        "lifecycle"
                    ) or {}).get("backend")) or {}
                ),
                "prod_server_error",
            ),
            (
                "PROD passerelle",
                (
                    (((snapshot.get("prod") or {}).get(
                        "lifecycle"
                    ) or {}).get("gateway")) or {}
                ),
                "prod_gateway_error",
            ),
            (
                "PROD Caddy",
                (
                    (((snapshot.get("prod") or {}).get(
                        "lifecycle"
                    ) or {}).get("caddy")) or {}
                ),
                "prod_caddy_error",
            ),
            (
                "LAB serveur",
                ((snapshot.get("lab") or {}).get("server") or {}),
                "lab_server_error",
            ),
            (
                "LAB Caddy",
                ((snapshot.get("lab") or {}).get("caddy") or {}),
                "lab_caddy_error",
            ),
        )
        for label, row, log_key in rows:
            ownership = str(row.get("ownership") or "").lower()
            alive = bool(row.get("process_alive"))
            http_ok = bool(row.get("http_alive"))
            if ownership == "foreign":
                issues.append({
                    "severity": "critical",
                    "code": "foreign_process",
                    "source": label.lower(),
                    "message": (
                        f"{label}: processus étranger sur le "
                        f"port géré (pid={row.get('pid')})."
                    ),
                    "log_key": log_key,
                })
            elif ownership == "orphan_exact":
                issues.append({
                    "severity": "warning",
                    "code": "orphan_exact",
                    "source": label.lower(),
                    "message": (
                        f"{label}: processus exact reconnu "
                        "mais non rattaché."
                    ),
                    "log_key": log_key,
                })
            if alive and not http_ok:
                issues.append({
                    "severity": "error",
                    "code": "http_unreachable",
                    "source": label.lower(),
                    "message": (
                        f"{label}: processus actif mais HTTP "
                        f"indisponible (pid={row.get('pid')})."
                    ),
                    "log_key": log_key,
                })

        for label, queue, log_key, backend_alive in (
            (
                "DEV",
                ((snapshot.get("dev") or {}).get("queue") or {}),
                "dev_server_error",
                bool(
                    ((snapshot.get("dev") or {}).get("server") or {}).get(
                        "process_alive"
                    )
                ),
            ),
            (
                "PROD",
                ((snapshot.get("prod") or {}).get("queue") or {}),
                "prod_server_error",
                bool(
                    (
                        (
                            (snapshot.get("prod") or {}).get("lifecycle")
                            or {}
                        ).get("backend")
                        or {}
                    ).get("process_alive")
                ),
            ),
            (
                "LAB",
                ((snapshot.get("lab") or {}).get("queue") or {}),
                "lab_server_error",
                bool(
                    ((snapshot.get("lab") or {}).get("server") or {}).get(
                        "process_alive"
                    )
                ),
            ),
        ):
            if backend_alive and queue.get("ok") is False:
                issues.append({
                    "severity": "error",
                    "code": "queue_error",
                    "source": label.lower(),
                    "message": (
                        f"{label}: erreur de lecture de queue — "
                        f"{queue.get('error') or 'erreur inconnue'}."
                    ),
                    "log_key": log_key,
                })

        circuit = self.lab_circuit.snapshot()
        if circuit.get("state") == "open":
            issues.append({
                "severity": "critical",
                "code": "lab_circuit_open",
                "source": "lab",
                "message": (
                    "LAB: circuit breaker ouvert après "
                    f"{circuit.get('failures')} échecs de relance."
                ),
                "log_key": "lab_server_error",
            })

        for item in self.log_tools.error_alerts():
            source = str(item.get("source") or "")
            issues.append({
                "severity": "error",
                "code": "log_error",
                "source": source,
                "message": str(
                    item.get("line") or "Erreur journalisée"
                )[:500],
                "log_key": self._log_key_for_source(source),
            })

        incidents = self.incidents.sync(issues)
        critical = sum(
            1
            for item in issues
            if str(item.get("severity") or "").lower()
            == "critical"
        )
        errors = sum(
            1
            for item in issues
            if str(item.get("severity") or "").lower()
            == "error"
        )
        warnings = sum(
            1
            for item in issues
            if str(item.get("severity") or "").lower()
            == "warning"
        )
        return {
            "state": (
                "ERROR"
                if critical or errors
                else "WARNING"
                if warnings
                else "OK"
            ),
            "critical": critical,
            "errors": errors,
            "warnings": warnings,
            "issues": issues[:30],
            "incidents": incidents[:30],
        }

    def _snapshot_uncached(self) -> dict:
        clear_process_cache()
        started = time.monotonic()
        dev = self.servers.view(Target.DEV)
        prod = self.prod.view()
        dev_caddy = self.caddy.view(Target.DEV)
        lab = self.servers.view(Target.LAB)
        lab_caddy = self.caddy.view(Target.LAB)
        elapsed_ms = round(
            (time.monotonic() - started) * 1000.0,
            1,
        )
        metrics = process_metrics(os.getpid())
        data = {
            "at": datetime.now(timezone.utc).isoformat(),
            "snapshot_ms": elapsed_ms,
            "analysis_active": bool(
                analysis_execution_active(self.runtime)
            ),
            "control_center": {
                "pid": os.getpid(),
                "executable_path": executable_path(
                    os.getpid()
                ),
                "command_line": command_line(os.getpid()),
                "cpu_percent": metrics.get("cpu_percent"),
                "ram_mb": metrics.get("ram_mb"),
            },
            "service": self._service_status(),
            "dev": {
                "server": asdict(dev),
                "caddy": asdict(dev_caddy),
                "queue": self._queue(Target.DEV),
                "analysis_python": str(
                    self.config.analysis_python_for(Target.DEV)
                ),
                "transport": self.config.transport_url_for(
                    Target.DEV
                ),
            },
            "prod": {
                "lifecycle": prod.as_dict(),
                "queue": self._queue(Target.PROD),
                "analysis_python": str(
                    self.config.analysis_python_for(Target.PROD)
                ),
                "transport": self.config.transport_url_for(
                    Target.PROD
                ),
            },
            "lab": {
                "server": asdict(lab),
                "caddy": asdict(lab_caddy),
                "queue": self._queue(Target.LAB),
                "workers": self._distributed_workers(),
                "analysis_python": str(
                    self.config.analysis_python_for(Target.LAB)
                ),
                "transport": self.config.transport_url_for(
                    Target.LAB
                ),
                "root": (
                    str(self.config.lab.root)
                    if self.config.lab is not None
                    else None
                ),
            },
        }
        data["safety"] = self._safety_status(data)
        return data

    def snapshot(self, force: bool = False) -> dict:
        with self.snapshot_lock:
            now = time.monotonic()
            if (
                not force
                and self._snapshot_cache is not None
                and (now - self._snapshot_cache_at) < SNAPSHOT_CACHE_SECONDS
            ):
                return self._snapshot_cache
            data = self._snapshot_uncached()
            self._snapshot_cache = data
            self._snapshot_cache_at = time.monotonic()
            return data

    def _invalidate_snapshot(self) -> None:
        with self.snapshot_lock:
            self._snapshot_cache = None
            self._snapshot_cache_at = 0.0
        clear_process_cache()

    def action(self, name: str) -> dict:
        with self.action_lock:
            if name == "dev-server-start":
                view = self.servers.start(Target.DEV)
                self._invalidate_snapshot()
                return {"ok": True, "message": f"Serveur DEV actif pid={view.pid}"}
            if name == "dev-server-stop":
                view = self.servers.stop(Target.DEV)
                self._invalidate_snapshot()
                return {"ok": True, "message": "Serveur DEV arrêté" if not view.process_alive else "Serveur DEV toujours actif"}
            if name == "dev-server-restart":
                view = self.servers.restart(Target.DEV)
                self._invalidate_snapshot()
                return {"ok": True, "message": f"Serveur DEV redémarré pid={view.pid}"}
            if name == "dev-caddy-start":
                view = self.caddy.start(Target.DEV)
                self._invalidate_snapshot()
                return {"ok": True, "message": f"DEV Caddy active pid={view.pid}"}

            if name == "lab-server-adopt":
                view = self.servers.adopt(Target.LAB)
                self._invalidate_snapshot()
                return {"ok": True, "message": f"Serveur LAB réadopté pid={view.pid}"}
            if name == "lab-circuit-reset":
                self.lab_circuit.reset()
                self._invalidate_snapshot()
                return {"ok": True, "message": "Protection LAB réinitialisée"}
            if name == "lab-server-start":
                view = self.servers.start(Target.LAB)
                self._invalidate_snapshot()
                return {"ok": True, "message": f"Serveur LAB actif pid={view.pid}"}
            if name == "lab-server-stop":
                view = self.servers.stop(Target.LAB)
                self._invalidate_snapshot()
                return {"ok": True, "message": "Serveur LAB arrêté" if not view.process_alive else "Serveur LAB toujours actif"}
            if name == "lab-server-restart":
                view = self.servers.restart(Target.LAB)
                self._invalidate_snapshot()
                return {"ok": True, "message": f"Serveur LAB redémarré pid={view.pid}"}
            if name == "lab-caddy-start":
                view = self.caddy.start(Target.LAB)
                self._invalidate_snapshot()
                return {"ok": True, "message": f"LAB Caddy active pid={view.pid}"}
            if name == "prod-start":
                view = self.prod.start("normal")
                self._invalidate_snapshot()
                return {"ok": view.online, "message": "PROD started in normal mode"}
            if name == "prod-stop":
                view = self.prod.stop()
                self._invalidate_snapshot()
                return {"ok": not view.online, "message": "PROD stopped"}
            if name == "prod-restart":
                view = self.prod.restart()
                self._invalidate_snapshot()
                return {"ok": view.online, "message": f"PROD restarted mode={view.mode}"}
            if name == "prod-maintenance-on":
                view = self.prod.set_maintenance(True)
                self._invalidate_snapshot()
                return {"ok": view.online, "message": "PROD maintenance ON"}
            if name == "prod-maintenance-off":
                view = self.prod.set_maintenance(False)
                self._invalidate_snapshot()
                return {"ok": view.online, "message": "PROD normal mode restored"}

            if name == "service-start-all":
                completed = subprocess.run(
                    [sys.executable, "-m", "service.service_cli", "start", "--target", "all", "--poll-seconds", "2"],
                    cwd=str(self.config.orchestrator_root),
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                self._invalidate_snapshot()
                output = (completed.stdout or completed.stderr).strip()
                return {"ok": completed.returncode in (0, 3), "message": output or f"returncode={completed.returncode}"}

            if name == "service-stop":
                completed = subprocess.run(
                    [sys.executable, "-m", "service.service_cli", "stop", "--wait-seconds", "15"],
                    cwd=str(self.config.orchestrator_root),
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                self._invalidate_snapshot()
                output = (completed.stdout or completed.stderr).strip()
                return {"ok": completed.returncode == 0, "message": output or f"returncode={completed.returncode}"}

            if name == "logs-clear":
                result = self.log_tools.clear_logs()
                if result.failed:
                    return {
                        "ok": False,
                        "message": f"Logs cleared={result.cleared}; failures={len(result.failed)}",
                        "failures": list(result.failed),
                    }
                return {"ok": True, "message": f"{result.cleared} log file(s) physically truncated"}

            raise ValueError(f"unsupported_action:{name}")

    # R3_21_QUEUE_VISIBILITY
    @staticmethod
    def _queued_job_row(target: Target, raw: dict, position: int) -> dict:
        row = raw if isinstance(raw, dict) else {}
        song = row.get("song") if isinstance(row.get("song"), dict) else {}
        raw_job_id = row.get("job_id", row.get("id"))
        try:
            job_id = int(raw_job_id) if raw_job_id is not None else None
        except (TypeError, ValueError):
            job_id = raw_job_id
        song_id = row.get("song_id")
        if song_id is None:
            song_id = song.get("id")
        song_title = row.get("title") or row.get("song_title") or song.get("title") or song.get("name")
        timestamp = row.get("queued_at") or row.get("created_at") or row.get("updated_at") or ""
        return {
            "job_id": job_id if job_id is not None else "-",
            "target": target.value,
            "song_id": song_id,
            "song_title": song_title,
            "kind": row.get("kind") or "-",
            "state": "waiting",
            "timestamp": str(timestamp or ""),
            "analysis_returncode": None,
            "finalize_status": "waiting",
            "returncode": None,
            "error": None,
            "run": None,
            "queue_position": int(position),
            "source": "live_queue",
        }

    @staticmethod
    def _job_key(row: dict):
        target = str(row.get("target") or "").strip().lower()
        job_id = row.get("job_id")
        if not target or job_id in (None, "", "-"):
            return None
        return target, str(job_id)

    def _r2e_canonical_jobs(self) -> list[dict]:
        """Read-only LAB canonical history, never claim or alter AI jobs."""
        lab_url = self.config.lab_backend_url
        if not lab_url:
            raise RuntimeError('lab_backend_url_missing')
        token = self.assistant_supervision._configured_token()
        url = lab_url.rstrip('/') + '/internal/analysis/desktop/profile/ai-requests/recent?limit=80'
        request = urllib.request.Request(url, headers={
            'X-EZScore-Analysis-Token': token,
            'Accept': 'application/json',
        }, method='GET')
        with urllib.request.urlopen(request, timeout=3) as response:
            payload = json.loads(response.read(262144).decode('utf-8'))
        raw = payload.get('jobs')
        if not isinstance(raw, list):
            raise ValueError('r2e_invalid_lab_job_history')
        records = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            status = str(item.get('status') or '').lower()
            if status not in {'queued', 'running', 'completed', 'error'}:
                continue
            records.append({
                'job_id': item.get('job_id'),
                'target': 'lab',
                'song_id': item.get('song_id'),
                'song_title': item.get('song_title') or f"PROFILE run #{item.get('run_id')}",
                'kind': 'assistant.profile.review',
                'state': status,
                'timestamp': item.get('updated_at') or item.get('created_at') or '',
                'analysis_returncode': None,
                'finalize_status': 'ok' if status == 'completed' else ('error' if status == 'error' else '-'),
                'error': item.get('message') if status == 'error' else None,
                'run_id': item.get('run_id'),
                'source': 'lab_canonical_ai',
            })
        return records

    def _lab_scientific_jobs(self, limit: int = 80) -> list[dict]:
        """Read the canonical LAB scientific PROFILE history without changing LAB.

        The existing AI history endpoint is specific to assistant.profile.review.
        Use a read-only SQLite connection for the separate scientific jobs.
        """
        database = Path(r"H:\EZStudio_lab\data\benchmark.sqlite")
        if not database.is_file():
            raise FileNotFoundError("lab_scientific_history_database_missing")
        connection = sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=2)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                """SELECT aj.id AS job_id, aj.scientific_run_id AS run_id,
                          aj.kind, aj.status, aj.created_at, aj.updated_at,
                          aj.song_id, s.title AS song_title, aj.error
                   FROM analysis_jobs aj
                   LEFT JOIN songs s ON s.id = aj.song_id
                   WHERE aj.kind = 'profile'
                   ORDER BY aj.id DESC LIMIT ?""", (max(1, min(limit, 100)),)
            ).fetchall()
        finally:
            connection.close()
        states = {"queued":"waiting", "running":"running", "completed":"completed",
                  "done":"completed", "failed":"failed", "error":"failed",
                  "cancelled":"cancelled"}
        return [{
            "job_id": int(row["job_id"]),
            "target": "lab",
            "song_id": row["song_id"],
            "song_title": row["song_title"] or f"PROFILE run #{row['run_id']}",
            "kind": "profile",
            "state": states.get(str(row["status"]).lower(), str(row["status"]).lower()),
            "timestamp": row["updated_at"] or row["created_at"] or "",
            "analysis_returncode": None,
            "finalize_status": "ok" if row["status"] == "completed" else "-",
            "error": str(row["error"])[:240] if row["status"] in ("failed", "error") and row["error"] else None,
            "run_id": row["run_id"],
            "source": "lab_scientific_read_only",
        } for row in rows]

    def jobs(self) -> dict:
        history_payload = self.job_history.payload(limit=80)
        history = list(history_payload.get("jobs") or [])
        known = {key for row in history if (key := self._job_key(row)) is not None}
        waiting = []
        queue_errors = {}
        try:
            canonical_ai = self._r2e_canonical_jobs()
        except Exception as exc:
            canonical_ai = []
            queue_errors['lab_ai'] = f"{type(exc).__name__}:{exc}"[:200]
        try:
            canonical_profile = self._lab_scientific_jobs()
        except Exception as exc:
            canonical_profile = []
            queue_errors["lab_profile_history"] = f"{type(exc).__name__}:{exc}"[:200]
        # Only deduplicate the same LAB job ID; never conflate analysis and IA.
        canonical_keys = {self._job_key(row) for row in canonical_profile}
        history = [row for row in history if self._job_key(row) not in canonical_keys]
        # Canonical LAB status supersedes historical scientific-worker errors for
        # the same ID; retain old unrelated scientific records distinctly.
        ai_keys = {self._job_key(row) for row in canonical_ai}
        history = [row for row in history if not (
            str(row.get('kind') or '') == 'assistant.profile.review'
            and self._job_key(row) in ai_keys
        )]
        known = {key for row in history + canonical_ai + canonical_profile for key in [self._job_key(row)] if key is not None}
        for target in (Target.DEV, Target.PROD, Target.LAB):
            try:
                queued = self.transport.queue(target)
            except Exception as exc:
                queue_errors[target.value] = f"{type(exc).__name__}:{exc}"[:500]
                continue
            for position, raw in enumerate(queued, start=1):
                row = self._queued_job_row(target, raw, position)
                key = self._job_key(row)
                if key is not None and key in known:
                    continue
                waiting.append(row)
                if key is not None:
                    known.add(key)
        active_states = {"running", "claimed", "cancelling"}
        active = [r for r in history if str(r.get("state") or "").lower() in active_states]
        archived = [r for r in history if str(r.get("state") or "").lower() not in active_states]
        profile_active = [r for r in canonical_profile if r["state"] in active_states]
        profile_waiting = [r for r in canonical_profile if r["state"] == "waiting"]
        profile_archived = [r for r in canonical_profile if r["state"] not in active_states and r["state"] != "waiting"]
        ai_active = [r for r in canonical_ai if r['state'] in active_states]
        ai_waiting = [r for r in canonical_ai if r['state'] == 'queued']
        ai_archived = [r for r in canonical_ai if r['state'] not in active_states and r['state'] != 'queued']
        # Interleave histories by real timestamp, not by provider type.
        jobs = profile_active + ai_active + active + profile_waiting + ai_waiting + waiting
        finished = profile_archived + ai_archived + archived
        finished.sort(key=lambda row: str(row.get("timestamp") or ""), reverse=True)
        jobs += finished
        return {
            "ok": bool(history_payload.get("ok", True)),
            "count": len(jobs),
            "jobs": jobs[:100],
            "running": len(active) + len(ai_active) + len(profile_active),
            "waiting": len(waiting) + len(ai_waiting) + len(profile_waiting),
            "history": len(archived) + len(ai_archived) + len(profile_archived),
            "queue_errors": queue_errors,
            "ai_canonical_count": len(canonical_ai),
            "execution_policy": "sequential_machine_gpu_singleton",
        }

    def logs(self) -> dict:
        root = self.config.orchestrator_root
        return {
            "service": self.log_tools.tail(root / "runtime" / "service" / "service.out.log"),
            "service_error": self.log_tools.tail(root / "runtime" / "service" / "service.err.log"),
            "control_center": self.log_tools.tail(root / "logs" / "control-center.log"),
            "control_center_error": self.log_tools.tail(root / "logs" / "control-center-error.log"),
            "dev_server_error": self.log_tools.tail(root / "logs" / "servers" / "dev.err.log"),
            "dev_caddy_error": self.log_tools.tail(root / "runtime" / "caddy" / "dev" / "caddy.err.log"),
            "prod_server_error": self.log_tools.tail(root / "logs" / "servers" / "prod.err.log"),
            "prod_gateway_error": self.log_tools.tail(root / "logs" / "gateway" / "prod.err.log"),
            "prod_caddy_error": self.log_tools.tail(root / "runtime" / "caddy" / "prod" / "caddy.err.log"),
            "lab_server_error": self.log_tools.tail(root / "logs" / "servers" / "lab.err.log"),
            "lab_caddy_error": self.log_tools.tail(root / "runtime" / "caddy" / "lab" / "caddy.err.log"),
            "assistant_deployment": self.log_tools.tail(root / "logs" / "assistant-deployment.log"),
        }

    def assistant_supervision_status(self) -> dict:
        remote = self.assistant_supervision.status()
        workers_payload = self._distributed_workers()
        workers = workers_payload.get("workers") if workers_payload.get("ok") else []
        workers = workers if isinstance(workers, list) else []
        online = [w for w in workers if isinstance(w, dict) and w.get("online")]
        states = {str(w.get("state") or "").lower() for w in online}

        # Runtime truth comes from the XPS process/listener probe. Inventory
        # heartbeats may enrich RUNNING but can never promote STOPPED/DEGRADED.
        remote_state = str(remote.get("state") or "ERROR").upper()
        if not remote.get("ok"):
            state = "ERROR"
        elif remote_state == "RUNNING":
            if states.intersection({"running", "busy", "claimed", "processing"}):
                state = "BUSY"
            else:
                state = "ONLINE"
        elif remote_state == "WEB_ONLY":
            state = "WEB_ONLY"
        elif remote_state == "DEGRADED":
            state = "DEGRADED"
        elif remote_state == "FOREIGN":
            state = "FOREIGN"
        elif remote_state == "STOPPED":
            state = "STOPPED"
        else:
            state = "ERROR"

        return {
            **remote,
            "state": state,
            "inventory_online": len(online),
            "inventory_count": len(workers),
        }

    def assistant_logs(self, stream: str) -> dict:
        return self.assistant_supervision.tail(stream)

    def assistant_start(self) -> dict:
        with self.action_lock:
            result = self.assistant_supervision.start()
            self._invalidate_snapshot()
            return result

    def assistant_stop(self) -> dict:
        with self.action_lock:
            result = self.assistant_supervision.stop()
            self._invalidate_snapshot()
            return result

    def assistant_deployment_status(self) -> dict:
        try:
            return get_assistant_deployment_status(build_assistant_status_plan())
        except Exception as exc:
            return {
                "ok": False,
                "schema": "ezs.assistant-deployment.status.v1",
                "state": "ERROR",
                "source_version": _read_version(
                    Path(r"H:\EZStudioLab_assistant") / "VERSION"
                ),
                "deployed_version": None,
                "source_dirty": None,
                "source_commit": None,
                "deployed_commit": None,
                "node": "steph@192.168.1.81",
                "remote_root": r"C:\EZStudioLab_assistant",
                "error": f"{type(exc).__name__}:{exc}"[:500],
            }

    def assistant_deployment_apply(self) -> dict:
        with self.action_lock:
            plan = build_assistant_deploy_plan()
            result = None
            runtime = None
            try:
                result = deploy_assistant_node(plan)
                runtime = self.assistant_supervision.start()
                if str(runtime.get("state") or "").upper() != "RUNNING":
                    raise RuntimeError(
                        f"assistant_post_deploy_runtime_not_running:{runtime.get('state')}"
                    )
                finalize_assistant_deployment(plan)
            except Exception as exc:
                rollback_error = None
                restart_error = None
                try:
                    rollback_assistant_deployment(plan)
                except Exception as rollback_exc:
                    rollback_error = f"{type(rollback_exc).__name__}:{rollback_exc}"
                else:
                    try:
                        self.assistant_supervision.start()
                    except Exception as restart_exc:
                        restart_error = f"{type(restart_exc).__name__}:{restart_exc}"
                detail = f"{type(exc).__name__}:{exc}"
                if rollback_error:
                    detail += f"; rollback={rollback_error}"
                if restart_error:
                    detail += f"; rollback_restart={restart_error}"
                raise RuntimeError(
                    f"assistant_post_deploy_validation_failed:{detail[:1200]}"
                ) from exc

            self._invalidate_snapshot()
            return {
                **(result or {}),
                "runtime": runtime,
                "finalized": True,
            }

    def acknowledge_incident(self, incident_id: str) -> dict:
        return {
            "ok": True,
            "incident": self.incidents.acknowledge(incident_id),
        }

    def deployment_plan(self) -> dict:
        return self.deployment.plan(fetch=True).as_dict()

    def deployment_history(self) -> list[dict]:
        return self.deployment.history(limit=30)

    def deployment_detail(self, deployment_id: str) -> dict:
        return self.deployment.detail(deployment_id)

    def deployment_apply(self, commit: str) -> dict:
        with self.action_lock:
            result = self.deployment.apply(commit)
            self._invalidate_snapshot()
            return result


HTML = r'''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EZS Orchestrator V__ORCH_VERSION__</title>
<style>
:root{color-scheme:dark;--bg:#0a1013;--panel:#10191e;--panel2:#152229;--line:#263840;--text:#edf5f4;--muted:#91a6ac;--accent:#49d1bd;--ok:#5ed38b;--warn:#f2c96d;--bad:#ff7b7b;--prod:#9da8ff;--side:236px;--sideCollapsed:72px}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,Segoe UI,Arial;background:var(--bg);color:var(--text)}
button,a.btn{appearance:none;border:1px solid var(--line);background:var(--panel2);color:var(--text);border-radius:9px;padding:9px 12px;text-decoration:none;cursor:pointer;font-weight:650}
button.primary,a.primary{background:#173b37;border-color:#27655d}button.danger{background:#371d21;border-color:#6f343c}button.warn{background:#3a3019;border-color:#6e5928}button:disabled{opacity:.45;cursor:not-allowed}
.shell{display:grid;grid-template-columns:var(--side) 1fr;min-height:calc(100vh - 68px);transition:grid-template-columns .18s ease}.shell.collapsed{grid-template-columns:var(--sideCollapsed) 1fr}
.sidebar{position:sticky;top:68px;height:calc(100vh - 68px);border-right:1px solid var(--line);background:#0d1519;padding:12px 10px;display:flex;flex-direction:column;gap:10px;overflow:hidden}
.brand{display:flex;align-items:center;gap:10px;padding:7px 8px;font-weight:850;letter-spacing:.04em;white-space:nowrap;min-height:48px}.brandMark{width:34px;height:34px;min-width:34px;min-height:34px;flex:0 0 34px;border-radius:9px;background:#173b37;display:grid;place-items:center;color:var(--accent)}.brandText b{color:var(--accent)}.brandText small{display:block;color:var(--muted);font-weight:500;letter-spacing:0}
.nav{display:grid;gap:6px;margin-top:8px}.nav button{width:100%;display:flex;align-items:center;gap:11px;text-align:left;background:transparent;border-color:transparent;padding:10px}.nav button.active{background:#17332f;border-color:#2e5d57}.ico{width:28px;text-align:center;font-size:18px;flex:0 0 28px}.navLabel,.brandText{transition:opacity .12s ease}.collapsed .navLabel,.collapsed .brandText{opacity:0;pointer-events:none}.collapsed .brand{justify-content:center;padding-left:0;padding-right:0}
.collapseRow{display:flex;justify-content:flex-end;padding:0 4px 4px}.collapseBtn{min-width:42px;padding:6px 9px;font-size:17px;line-height:1;font-weight:900;background:#0d1519;border-color:#36505b;color:var(--text)}.collapsed .collapseRow{justify-content:center}.collapsed .collapseBtn{min-width:42px}.content{min-width:0}.topbar{position:sticky;top:0;z-index:30;height:68px;width:100%;display:flex;align-items:center;justify-content:space-between;gap:22px;padding:0 20px;border-bottom:1px solid #35505a;background:#0b1418;box-shadow:0 4px 18px rgba(0,0,0,.28)}.headerLeft{display:flex;align-items:center;gap:16px;min-width:0}.appHeader{display:flex;align-items:center;gap:10px;min-width:0}.appHeaderMark{width:32px;height:32px;flex:0 0 32px;border-radius:8px;background:#173b37;display:grid;place-items:center;color:var(--accent);font-weight:850}.appHeaderName{font-weight:850;letter-spacing:.03em;white-space:nowrap}.appHeaderName b{color:var(--accent)}.viewContext{padding-left:16px;border-left:1px solid var(--line);min-width:0}.topTitle{font-size:17px;font-weight:800;white-space:nowrap}.topSubtitle{color:var(--muted);font-size:12px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:520px}.headerRight{display:flex;align-items:center;gap:10px}.globalBadge{padding:6px 10px;border-radius:999px;border:1px solid #2b6c49;background:#11251c;color:var(--ok);font-size:12px;font-weight:750;white-space:nowrap}.globalBadge.busy{border-color:#775a27;background:#251f13;color:var(--warn)}.topMeta{color:var(--muted);font-size:12px;text-align:right;white-space:nowrap}.headerRefresh{padding:7px 10px}
main{padding:20px;max-width:1600px;margin:auto}.view{display:none}.view.active{display:block}.banner{margin-bottom:14px;padding:11px 14px;border:1px solid var(--line);border-radius:10px;background:var(--panel)}.banner.active{border-color:#775a27;background:#251f13}
.grid3{display:grid;grid-template-columns:1.15fr 1fr 1fr;gap:14px}.grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px}.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;min-width:0}.card h2{margin:0 0 12px;font-size:14px}.statusrow{display:flex;align-items:center;gap:9px;flex-wrap:wrap}.dot{width:10px;height:10px;border-radius:50%;background:var(--muted)}.dot.ok{background:var(--ok)}.dot.warn{background:var(--warn)}.dot.bad{background:var(--bad)}.big{font-size:22px;font-weight:780;margin:6px 0}.muted{color:var(--muted)}.lock{padding:8px 10px;background:#151727;border:1px solid #30355f;border-radius:9px;color:#bfc5ff;font-size:12px}.target.dev{border-top:3px solid var(--accent)}.target.prod{border-top:3px solid var(--prod)}.target.lab{border-top:3px solid var(--warn)}.assistantNode{border:1px solid var(--line);border-radius:10px;padding:10px 12px;margin-top:8px;background:#0c1519}.assistantNode strong{display:block;margin-bottom:4px}.assistantMeta{display:grid;grid-template-columns:120px minmax(0,1fr);gap:4px 8px;font-size:12px}.assistantMeta span:nth-child(odd){color:var(--muted)}
.kv{display:grid;grid-template-columns:150px minmax(0,1fr);gap:7px 10px;margin:10px 0}.kv dt{color:var(--muted)}.kv dd{margin:0;overflow-wrap:anywhere}.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}.mode{padding:3px 8px;border-radius:999px;border:1px solid var(--line);font-size:12px}.mode.maintenance{background:#3a3019;border-color:#6e5928;color:var(--warn)}
.tablewrap{overflow:auto;border:1px solid var(--line);border-radius:10px}.datatable{width:100%;border-collapse:collapse;min-width:880px}.datatable th,.datatable td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}.datatable th{color:var(--muted);font-size:12px;background:#0d1519}.job-state{font-weight:750}.job-state.completed{color:var(--ok)}.job-state.failed{color:var(--bad)}.job-state.finalize_error{color:var(--warn)}.job-state.running,.job-state.claimed,.job-state.queued,.job-state.waiting,.job-state.cancelling{color:var(--warn)}.job-target{font-weight:750}.job-target.dev{color:var(--accent)}.job-target.prod{color:var(--prod)}.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 8px}.tab.active{border-color:#397168;background:#17332f}pre{white-space:pre-wrap;word-break:break-word;background:#080d10;border:1px solid var(--line);padding:12px;border-radius:10px;max-height:360px;overflow:auto;color:#cbd8da}.deployConsole{min-height:180px;max-height:300px;font-family:Consolas,monospace}.deployConsole.running{border-color:#775a27}.deployConsole.completed{border-color:#2b6c49}.deployConsole.failed{border-color:#74383e}
.queueCard strong{font-size:20px}.queueList{display:grid;gap:6px;margin-top:10px}.queueRow{padding:8px 9px;border:1px solid var(--line);border-radius:8px;background:#0d1519}.deployDecision{font-size:24px;font-weight:850}.deployDecision.ok{color:var(--ok)}.deployDecision.bad{color:var(--bad)}.deployDecision.idle{color:var(--muted)}.checks{display:grid;gap:7px}.check{padding:8px 10px;border:1px solid var(--line);border-radius:8px}.check.ok{border-color:#2b6c49}.check.bad{border-color:#74383e;background:#2a1518}.sensitive{color:var(--warn);font-weight:750}.history{display:grid;gap:7px}.history button{text-align:left;width:100%}.toast{position:fixed;right:18px;bottom:18px;max-width:720px;padding:10px 14px;border-radius:10px;background:#172228;border:1px solid var(--line);display:none;z-index:20}.toast.show{display:block}.toast.ok{border-color:#2b6c49}.toast.bad{border-color:#74383e}
.modalBackdrop{position:fixed;inset:0;z-index:80;display:none;align-items:center;justify-content:center;padding:24px;background:rgba(0,0,0,.62);backdrop-filter:blur(3px)}.modalBackdrop.show{display:flex}.modal{width:min(720px,calc(100vw - 40px));max-height:calc(100vh - 48px);overflow:auto;border:1px solid #35505a;border-radius:14px;background:#0f191e;box-shadow:0 24px 70px rgba(0,0,0,.55)}.modalHead{padding:18px 20px;border-bottom:1px solid var(--line)}.modalHead h3{margin:0 0 4px;font-size:20px}.modalBody{padding:18px 20px;display:grid;gap:16px}.modalSummary{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:10px}.modalStat{border:1px solid var(--line);border-radius:10px;padding:10px 12px;background:#0c1519}.modalStat b{display:block;font-size:18px;margin-top:3px}.modalSteps{display:grid;gap:8px;margin:0;padding:0;list-style:none}.modalSteps li{padding:9px 10px;border:1px solid var(--line);border-radius:8px;background:#0c1519}.modalWarn{padding:11px 12px;border:1px solid #775a27;border-radius:9px;background:#251f13;color:var(--warn)}.modalFoot{display:flex;justify-content:flex-end;gap:10px;padding:16px 20px;border-top:1px solid var(--line)}@media(max-width:700px){.modalSummary{grid-template-columns:1fr}.modal{width:calc(100vw - 20px)}}@media(max-width:1000px){.grid3,.grid2{grid-template-columns:1fr}.shell{grid-template-columns:var(--sideCollapsed) 1fr}.navLabel,.brandText{display:none}.kv{grid-template-columns:120px minmax(0,1fr)}.appHeaderName{display:none}.viewContext{border-left:0;padding-left:0}.headerRight{gap:6px}.topMeta{display:none}}
.safetyBanner{display:flex;align-items:center;justify-content:space-between;gap:14px;margin:0 0 14px;padding:12px 14px;border:1px solid #295747;border-radius:10px;background:#10231d}
.safetyBanner.warning{border-color:#775a27;background:#251f13}.safetyBanner.error{border-color:#7a3138;background:#2b1519}
.safetyBanner strong{display:block}.safetyBanner .detail{margin-top:3px;color:var(--muted);font-size:12px;max-width:980px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.safetyBanner.error strong{color:var(--bad)}.safetyBanner.warning strong{color:var(--warn)}
.safetyBanner button{display:none;white-space:nowrap}.safetyBanner.error button,.safetyBanner.warning button{display:inline-block}
.incidentPanel{margin:0 0 14px;border:1px solid var(--line);border-radius:10px;background:#0d1519;padding:10px 12px}.incidentList{display:grid;gap:6px}.incidentRow{display:grid;grid-template-columns:90px 1fr auto;gap:10px;align-items:center;border:1px solid var(--line);border-radius:8px;padding:8px 10px}.incidentLevel{font-weight:800}.incidentLevel.CRITICAL,.incidentLevel.ERROR{color:var(--bad)}.incidentLevel.WARNING{color:var(--warn)}.incidentLevel.INFO{color:var(--accent)}

</style>
</head>
<body>
<header class="topbar">
  <div class="headerLeft">
    <div class="appHeader">
      <div class="appHeaderMark">EZ</div>
      <div class="appHeaderName"><b>EZS</b> ORCHESTRATOR <span class="muted">V__ORCH_VERSION__</span></div>
    </div>
    <div class="viewContext">
      <div id="viewTitle" class="topTitle">Infrastructure</div>
      <div class="topSubtitle">ORCH V__ORCH_VERSION__ · DEV V__DEV_VERSION__ · LAB V__LAB_VERSION__ · ASSISTANT V__ASSISTANT_VERSION__</div>
    </div>
  </div>
  <div class="headerRight">
    <div id="globalState" class="globalBadge">Chargement…</div>
    <div id="updated" class="topMeta">-</div>
    <button id="headerRefresh" class="headerRefresh" type="button">Actualiser</button>
  </div>
</header>
<div id="shell" class="shell">
<aside class="sidebar">
  <div class="collapseRow"><button id="collapse" class="collapseBtn" type="button" aria-label="Réduire le volet" title="Réduire le volet">&lt;&lt;</button></div>
  <nav class="nav">
    <button class="active" data-view="infrastructure"><span class="ico">◫</span><span class="navLabel">Infrastructure</span></button>
    <button data-view="queues"><span class="ico">≣</span><span class="navLabel">Queues & Jobs</span></button>
    <button data-view="logs"><span class="ico">▤</span><span class="navLabel">Logs</span></button>
    <button data-view="deployment"><span class="ico">⇧</span><span class="navLabel">Déploiement</span></button>
  </nav>
</aside>
<div class="content">
<main>
<div id="analysisBanner" class="banner">État d'exécution en cours de lecture…</div>
<div id="safetyBanner" class="safetyBanner">
  <div>
    <strong id="safetyTitle">Supervision processus : lecture…</strong>
    <div id="safetyDetail" class="detail">Contrôle des processus, queues et erreurs visibles.</div>
  </div>
  <button id="safetyLogs" type="button">Voir logs</button>
</div>

<div id="incidentPanel" class="incidentPanel"><strong>Incidents opérationnels</strong><span id="incidentCount" class="muted" style="margin-left:10px">0 actif</span><div id="incidentList" class="incidentList" style="margin-top:8px"><div class="muted">(aucun)</div></div></div>

<section id="view-infrastructure" class="view active">
  <section class="grid3">
    <article class="card"><h2>Service permanent</h2><div class="statusrow"><span id="serviceDot" class="dot"></span><span id="serviceState">-</span></div><div class="big" id="serviceTarget">-</div><div class="muted" id="serviceMeta">-</div><div class="actions"><button id="serviceStart" class="primary">Démarrer service DEV + PROD + LAB</button><button id="serviceStop">Arrêter service</button></div></article>
    <article class="card"><h2>GPU / exécution</h2><div class="statusrow"><span id="gpuDot" class="dot"></span><span id="gpuState">-</span></div><div class="big">1 slot GPU</div><div class="muted">Singleton machine-wide protégé.</div></article>
    <article class="card"><h2>Politique de sûreté</h2><div class="lock">DEV, PROD et LAB restent physiquement isolés. Les actions destructives sont bloquées pendant une analyse.</div><div class="muted" style="margin-top:10px">Les diagnostics n'exportent pas runtime/jobs ni les données métier.</div></article>
  </section>
  <section class="grid2" style="margin-top:14px">
    <article class="card target dev"><h2>DEV · V__DEV_VERSION__</h2><div class="statusrow"><span id="devDot" class="dot"></span><strong id="devState">-</strong></div><dl class="kv"><dt>Répertoire</dt><dd id="devRoot">-</dd><dt>APP_ENV</dt><dd id="devEnv">-</dd><dt>Serveur</dt><dd id="devBackend">-</dd><dt>Caddy</dt><dd id="devCaddy">-</dd><dt>URL serveur</dt><dd id="devTransport">-</dd><dt>Python analyse</dt><dd id="devPython">-</dd><dt>Propriété processus</dt><dd id="devOwnership">-</dd></dl><div class="actions"><button data-action="dev-server-start" class="primary">Démarrer serveur</button><button data-action="dev-server-restart">Redémarrer serveur</button><button data-action="dev-server-stop" data-destructive="1" class="danger">Arrêter serveur</button><button data-action="dev-caddy-start">Démarrer Caddy</button><a class="btn primary" href="http://127.0.0.1:8502/fr/catalog" target="_blank" rel="noreferrer">Ouvrir DEV</a></div></article>
    <article class="card target prod"><h2>PROD · exploitation protégée</h2><div class="statusrow"><span id="prodDot" class="dot"></span><strong id="prodState">-</strong><span id="prodMode" class="mode">-</span></div><dl class="kv"><dt>Répertoire</dt><dd id="prodRoot">-</dd><dt>APP_ENV</dt><dd>prod</dd><dt>Serveur :8511</dt><dd id="prodBackend">-</dd><dt>Passerelle :8510</dt><dd id="prodGateway">-</dd><dt>Caddy :8501</dt><dd id="prodCaddy">-</dd><dt>URL serveur</dt><dd id="prodTransport">-</dd><dt>Python analyse</dt><dd id="prodPython">-</dd><dt>Propriété processus</dt><dd id="prodOwnership">-</dd></dl><div class="actions"><button data-action="prod-start" class="primary">Démarrer PROD</button><button data-action="prod-restart" data-destructive="1">Redémarrer PROD</button><button data-action="prod-stop" data-destructive="1" class="danger">Arrêter PROD</button><button data-action="prod-maintenance-off">Mode normal</button><button data-action="prod-maintenance-on" class="warn">Maintenance</button><a class="btn primary" href="https://ezscore.logandplay.com/fr/catalog" target="_blank" rel="noreferrer">Ouvrir PROD</a></div></article>
  </section>
  <section class="grid2" style="margin-top:14px">
    <article class="card target lab">
      <h2>LAB · V__LAB_VERSION__ · expérimentation isolée</h2>
      <div class="statusrow"><span id="labDot" class="dot"></span><strong id="labState">-</strong></div>
      <dl class="kv">
        <dt>Répertoire</dt><dd id="labRoot">-</dd>
        <dt>APP_ENV</dt><dd id="labEnv">-</dd>
        <dt>Serveur</dt><dd id="labBackend">-</dd>
        <dt>Caddy LAN</dt><dd id="labCaddy">-</dd>
        <dt>URL serveur</dt><dd id="labTransport">-</dd>
        <dt>Python analyse</dt><dd id="labPython">-</dd>
        <dt>Propriété processus</dt><dd id="labOwnership">-</dd>
      </dl>
      <div class="actions">
        <button data-action="lab-server-start" class="primary">Démarrer serveur</button>
        <button data-action="lab-server-adopt">Réadopter serveur</button>
        <button data-action="lab-circuit-reset">Reset protection LAB</button>
        <button data-action="lab-server-restart">Redémarrer serveur</button>
        <button data-action="lab-server-stop" data-destructive="1" class="danger">Arrêter serveur</button>
        <button data-action="lab-caddy-start">Démarrer Caddy LAB</button>
        <a class="btn primary" href="http://127.0.0.1:8701/" target="_blank" rel="noreferrer">Ouvrir LAB</a>
      </div>
    </article>
    <article class="card target lab">
      <h2>EZStudioLab_assistant · V__ASSISTANT_VERSION__ · nœuds distribués</h2>
      <div class="statusrow"><span id="assistantDot" class="dot"></span><strong id="assistantState">-</strong></div>
      <div class="muted" id="assistantMeta" style="margin-top:6px">Inventaire en lecture seule.</div>
      <dl class="kv" style="margin-top:10px">
        <dt>Version source</dt><dd id="assistantSourceVersion">-</dd>
        <dt>Version déployée</dt><dd id="assistantDeployedVersion">-</dd>
        <dt>État déploiement</dt><dd id="assistantDeployState">-</dd>
        <dt>Processus assistant XPS</dt><dd id="assistantRuntimeState">-</dd>
      </dl>
      <details style="margin-top:8px">
        <summary class="muted">Détails techniques Git</summary>
        <dl class="kv" style="margin-top:8px">
          <dt>Build source</dt><dd id="assistantSourceCommit">-</dd>
          <dt>Build déployé</dt><dd id="assistantDeployedCommit">-</dd>
        </dl>
      </details>
      <div id="assistantDeployNotice" class="muted" style="margin-top:10px"></div>
      <div class="actions">
        <button id="assistantStart" class="primary">Démarrer assistant</button>
        <button id="assistantStop" class="danger">Arrêter assistant</button>
        <button id="assistantDeploy">Déployer assistant → XPS</button>
      </div>
      <div id="assistantWorkers"></div>
    </article>
  </section>
  </section>

<section id="view-queues" class="view">
  <section class="card"><div style="display:flex;justify-content:space-between;gap:12px"><h2>Jobs récents</h2><span class="muted" id="jobsMeta">Chargement…</span></div><div class="tablewrap"><table class="datatable"><thead><tr><th>Job</th><th>Cible</th><th>Chanson</th><th>Type</th><th>État</th><th>Date</th><th>RC analyse</th><th>Finalisation</th><th>Erreur</th></tr></thead><tbody id="jobsBody"><tr><td colspan="9">Chargement…</td></tr></tbody></table></div></section>
</section>

<section id="view-logs" class="view">
  <section class="card">
    <div style="display:flex;align-items:center;justify-content:space-between;gap:12px">
      <div><h2 style="margin-bottom:4px">Logs</h2><div class="muted">Infrastructure, Orchestrator et déploiements</div></div>
    </div>
<div class="actions"><button id="clearLogs" class="danger">Clear logs</button><button id="exportLogs" class="primary">Export logs ZIP</button></div><div class="tabs"><button class="tab active" data-log="service">Service</button><button class="tab" data-log="service_error">Service erreurs</button><button class="tab" data-log="control_center">Orchestrator</button><button class="tab" data-log="control_center_error">Orchestrator erreurs</button><button class="tab" data-log="dev_server_error">Serveur DEV</button><button class="tab" data-log="dev_caddy_error">Caddy DEV</button><button class="tab" data-log="prod_server_error">Serveur PROD</button><button class="tab" data-log="prod_gateway_error">Passerelle PROD</button><button class="tab" data-log="prod_caddy_error">Caddy PROD</button><button class="tab" data-log="lab_server_error">Serveur LAB</button><button class="tab" data-log="lab_caddy_error">Caddy LAB</button><button class="tab" data-log="assistant_xps">Assistant XPS</button><button class="tab" data-log="assistant_xps_error">Assistant XPS erreurs</button><button class="tab" data-log="assistant_deployment">Déploiement assistant → XPS</button><button class="tab" data-log="deployments">Déploiement DEV → PROD</button></div><pre id="logText">Chargement…</pre></section>

  </section>
</section>

<section id="view-deployment" class="view">
  <section class="grid3">
    <article class="card"><h2>DEV · H:\EZScore_dev</h2><div id="deployDevSha" class="big">-</div><div id="deployDevMeta" class="muted">-</div></article>
    <article class="card"><h2>PROD · H:\EZScore</h2><div id="deployProdSha" class="big">-</div><div id="deployProdMeta" class="muted">-</div></article>
    <article class="card"><h2>Décision</h2><div id="deployDecision" class="deployDecision">-</div><div id="deployReasons" class="muted">-</div></article>
  </section>
  <section class="grid3" style="margin-top:14px">
    <article class="card"><h2>Préflight</h2><div id="deployChecks" class="checks"></div></article>
    <article class="card"><h2>Impact</h2><dl class="kv"><dt>Fichiers</dt><dd id="deployFiles">-</dd><dt>Sensibles</dt><dd id="deploySensitive">-</dd><dt>Migrations Doctrine</dt><dd id="deployMigrations">-</dd><dt>PHP PROD</dt><dd id="deployPhp">-</dd><dt>Composer</dt><dd id="deployComposer">-</dd></dl></article>
    <article class="card"><h2>Action</h2><div class="muted" id="deployTarget">-</div><div class="actions"><button id="deployRefresh">Actualiser l'analyse</button><button id="deployApply" class="warn" disabled>Déployer DEV → PROD</button></div><div class="muted" style="margin-top:10px">Le préflight est recalculé au clic. Aucun push Git, aucune copie DEV → PROD.</div></article>
  </section>
  <section class="card" style="margin-top:14px">
    <div style="display:flex;justify-content:space-between;gap:12px;align-items:center">
      <div><h2 style="margin-bottom:4px">Progression du déploiement</h2><div id="deployProgressState" class="muted">Aucun déploiement en cours.</div></div>
    </div>
    <pre id="deployProgress" class="deployConsole">En attente d’un déploiement.</pre>
  </section>
  <section class="card" style="margin-top:14px"><h2>Diff DEV → PROD</h2><div class="tablewrap"><table class="datatable"><thead><tr><th>État</th><th>Zone</th><th>Fichier</th><th>Protection</th><th>Sensibilité</th></tr></thead><tbody id="deployDiff"></tbody></table></div></section>
  <section class="grid2" style="margin-top:14px"><article class="card"><h2>Historique</h2><div id="deployHistory" class="history"></div></article><article class="card"><h2>Journal détaillé</h2><pre id="deployLog">Sélectionner un déploiement.</pre></article></section>
</section>

<div id="deployModalBackdrop" class="modalBackdrop" role="dialog" aria-modal="true" aria-labelledby="deployModalTitle">
  <div class="modal">
    <div class="modalHead">
      <h3 id="deployModalTitle">Confirmer le déploiement DEV → PROD</h3>
      <div class="muted" id="deployModalCommit">-</div>
    </div>
    <div class="modalBody">
      <div class="modalSummary">
        <div class="modalStat">Fichiers modifiés<b id="deployModalFiles">-</b></div>
        <div class="modalStat">Migrations Doctrine<b id="deployModalMigrations">-</b></div>
        <div class="modalStat">Fichiers sensibles<b id="deployModalSensitive">-</b></div>
      </div>
      <div>
        <h2 style="margin-bottom:8px">Ce qui va se passer</h2>
        <ul class="modalSteps">
          <li>Mettre en pause le worker d’analyse</li>
          <li>Passer PROD en maintenance</li>
          <li>Sauvegarder la base de données PROD</li>
          <li>Mettre à jour le code PROD vers la version DEV validée</li>
          <li>Installer les dépendances nécessaires</li>
          <li>Appliquer les migrations de base de données</li>
          <li>Vider le cache applicatif</li>
          <li>Redémarrer PROD</li>
          <li>Vérifier que PROD répond correctement</li>
          <li>Relancer le worker d’analyse</li>
        </ul>
      </div>
      <div class="modalWarn">
        Aucune donnée métier DEV n’est copiée vers PROD. En cas d’échec, PROD reste en maintenance afin d’éviter une remise en service partielle.
      </div>
    </div>
    <div class="modalFoot">
      <button id="deployModalCancel" type="button">Annuler</button>
      <button id="deployModalConfirm" class="primary" type="button">Déployer vers PROD</button>
    </div>
  </div>
</div>
<div id="toast" class="toast" role="status" aria-live="polite"></div>
</main></div></div>
<script>
const TOKEN="__TOKEN__";
let currentLog="service",busy=false,analysisActive=false,refreshInFlight=false,jobsRefreshInFlight=false,currentView="infrastructure",deployData=null;
let devFailures=0,prodFailures=0,labFailures=0;
const $=id=>document.getElementById(id);
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
function txt(id,v){const e=$(id);if(e)e.textContent=v??"-"}
function dot(el,ok,warn=false){el.className="dot "+(ok?"ok":warn?"warn":"bad")}
function toast(message,ok=true){const el=$("toast");el.textContent=message;el.className="toast show "+(ok?"ok":"bad");setTimeout(()=>el.className="toast",4500)}
async function getJSON(url){const r=await fetch(url,{cache:"no-store"});const data=await r.json();if(!r.ok)throw new Error(data.error||data.message||JSON.stringify(data));return data}
async function protectedFetch(url,options){const r=await fetch(url,options);if(r.status===403){window.location.reload();throw new Error("Session locale renouvelée. Rechargement de la page…")}return r}
function fmtMetric(v){return `CPU ${v?.cpu_percent==null?'-':v.cpu_percent+'%'} · RAM ${v?.ram_mb==null?'-':v.ram_mb+' MB'}`}
function fmtProc(v){return `pid ${v.pid??'-'} · ${v.process_alive?'PROCESSUS OK':'PROCESSUS ARRÊTÉ'} · ${v.http_alive?'HTTP OK':'HTTP KO'} · ${fmtMetric(v)}`}
function fmtOwnership(v){const x=String(v??"-").toLowerCase();return x==="owned"?"géré":x==="adopted"?"réadopté":x==="orphan_exact"?"orphelin reconnu":x==="orphan"?"orphelin":v??"-"}
function fmtWorkerState(v){const x=String(v??"-").toLowerCase();const labels={idle:"DISPONIBLE",online:"EN LIGNE",running:"OCCUPÉ",busy:"OCCUPÉ",claimed:"OCCUPÉ",processing:"OCCUPÉ",stale:"PÉRIMÉ",stopped:"ARRÊTÉ",error:"ERREUR"};return labels[x]||String(v??"-").toUpperCase()}

function setView(name){
 currentView=name;
 document.querySelectorAll(".view").forEach(v=>v.classList.toggle("active",v.id===`view-${name}`));
 document.querySelectorAll(".nav button[data-view]").forEach(b=>b.classList.toggle("active",b.dataset.view===name));
 txt("viewTitle",name==="infrastructure"?"Infrastructure":name==="queues"?"Queues & Jobs":name==="logs"?"Logs":"Déploiement");
 if(name==="deployment")refreshDeployment();
}
document.querySelectorAll(".nav button[data-view]").forEach(b=>b.addEventListener("click",()=>setView(b.dataset.view)));
function syncCollapseControl(){
 const sh=$("shell"),btn=$("collapse"),collapsed=sh.classList.contains("collapsed");
 btn.textContent=collapsed?">>":"<<";
 btn.setAttribute("aria-label",collapsed?"Déployer le volet":"Réduire le volet");
 btn.title=collapsed?"Déployer le volet":"Réduire le volet";
}
$("collapse").addEventListener("click",()=>{const sh=$("shell");sh.classList.toggle("collapsed");localStorage.setItem("ezs.sidebar.collapsed",sh.classList.contains("collapsed")?"1":"0");syncCollapseControl()});
if(localStorage.getItem("ezs.sidebar.collapsed")==="1")$("shell").classList.add("collapsed");
syncCollapseControl();

function syncActionButtons(){
 document.querySelectorAll('button[data-action]').forEach(b=>{const destructive=b.dataset.destructive==="1";b.disabled=busy||(destructive&&analysisActive)});
 if(deployData)$("deployApply").disabled=busy||analysisActive||!deployData.ok;
 if($("assistantDeploy"))$("assistantDeploy").disabled=busy||assistantDeployData?.state==="UP_TO_DATE"||assistantDeployData?.state==="UNREACHABLE"||assistantDeployData?.state==="LOCAL_CHANGES";
}
let assistantDeployData=null,assistantDeployRefreshInFlight=false;
function renderAssistantDeployment(payload){
 assistantDeployData=payload||{};
 const state=assistantDeployData.state||"ERROR";
 const sourceVersion=assistantDeployData.source_version||"-";
 const deployedVersion=assistantDeployData.deployed_version||"-";
 txt("assistantSourceVersion",sourceVersion==="-"?"-":`v${String(sourceVersion).replace(/^v/i,"")}`);
 txt("assistantDeployedVersion",deployedVersion==="-"?"-":`v${String(deployedVersion).replace(/^v/i,"")}`);
 txt("assistantSourceCommit",(assistantDeployData.source_commit||"").slice(0,12)||"-");
 txt("assistantDeployedCommit",(assistantDeployData.deployed_commit||"").slice(0,12)||"-");
 const label=state==="UP_TO_DATE"?"À JOUR":state==="LOCAL_CHANGES"?"MODIFICATIONS LOCALES":state==="UPDATE_AVAILABLE"?"MISE À JOUR DISPONIBLE":state==="NOT_DEPLOYED"?"NON DÉPLOYÉ":state==="UNREACHABLE"?"XPS INJOIGNABLE":"ERREUR";
 txt("assistantDeployState",label);
 const sourceLabel=sourceVersion==="-"?"la version locale":`v${String(sourceVersion).replace(/^v/i,"")}`;
 const deployedLabel=deployedVersion==="-"?"la version déployée":`v${String(deployedVersion).replace(/^v/i,"")}`;
 const notices={
  LOCAL_CHANGES:`⚠ Déploiement impossible : ${sourceLabel} contient des modifications locales non publiées. Commit/push Assistant requis, puis mise à jour du gitlink LAB avant déploiement.`,
  UPDATE_AVAILABLE:`✓ ${sourceLabel} est publiée et prête à être déployée vers XPS. Version actuellement déployée : ${deployedLabel}.`,
  UP_TO_DATE:`✓ ${sourceLabel} est déjà déployée sur XPS.`,
  NOT_DEPLOYED:`Assistant non déployé sur XPS.`,
  UNREACHABLE:`⚠ XPS est injoignable : déploiement indisponible.`,
  ERROR:`⚠ État de déploiement indisponible : ${assistantDeployData.error||"erreur inconnue"}.`
 };
 txt("assistantDeployNotice",notices[state]||"");
 const btn=$("assistantDeploy");
 if(btn){
  btn.disabled=busy||state==="UP_TO_DATE"||state==="UNREACHABLE"||state==="LOCAL_CHANGES";
  btn.title=state==="LOCAL_CHANGES"?"Commit/push Assistant puis mise à jour du gitlink LAB requis avant déploiement":"";
 }
}
async function refreshAssistantDeployment(){
 if(assistantDeployRefreshInFlight)return;
 assistantDeployRefreshInFlight=true;
 try{
  renderAssistantDeployment(await getJSON("/api/assistant/deployment/status"));
 }catch(e){
  renderAssistantDeployment({ok:false,state:"ERROR",error:String(e)});
 }finally{
  assistantDeployRefreshInFlight=false;
 }
}

let assistantSupervisionData=null,assistantSupervisionRefreshInFlight=false;
function renderAssistantSupervision(payload){
 assistantSupervisionData=payload||{};
 const state=assistantSupervisionData.state||"ERROR";
 const labels={STOPPED:"ARRÊTÉ",ONLINE:"EN LIGNE",BUSY:"OCCUPÉ",DEGRADED:"DÉGRADÉ",FOREIGN:"PORT ÉTRANGER",ERROR:"ERREUR"};
 const label=labels[state]||state;
 txt("assistantRuntimeState",label);
 txt("assistantState",label);
 dot($("assistantDot"),state==="ONLINE"||state==="BUSY",state==="DEGRADED");
 const running=state==="ONLINE"||state==="BUSY";
 const degraded=state==="DEGRADED";
 const blocked=state==="FOREIGN";
 const active=running||degraded;
 if($("assistantStart"))$("assistantStart").disabled=busy||running||blocked;
 if($("assistantStop"))$("assistantStop").disabled=busy||!active;
}
async function refreshAssistantSupervision(){
 if(assistantSupervisionRefreshInFlight)return;
 assistantSupervisionRefreshInFlight=true;
 try{
  renderAssistantSupervision(await getJSON("/api/assistant/supervision/status"));
 }catch(e){
  renderAssistantSupervision({ok:false,state:"ERROR",error:String(e)});
 }finally{
  assistantSupervisionRefreshInFlight=false;
 }
}

function renderAssistantWorkers(payload){
 const workers=(payload&&payload.workers)||[];
 const online=workers.filter(w=>!!w.online);
 txt("assistantMeta",payload&&payload.ok?`${online.length} worker(s) en ligne · ${workers.length} nœud(s) enregistré(s) · inventaire lecture seule`:`Inventaire indisponible · ${payload?.error??"-"}`);
 const el=$("assistantWorkers");
 el.innerHTML=workers.length?workers.map(w=>{
   const c=w.capabilities||{},g=(c.gpus||[])[0]||{};
   const gpu=g.name||"GPU non déclaré";
   const vram=g.vram_total_mb??c.max_vram_mb??"-";
   return `<div class="assistantNode"><strong>${esc(w.worker_id||"-")} · ${w.online?"EN LIGNE":"PÉRIMÉ"}</strong><div class="assistantMeta"><span>État</span><span>${esc(fmtWorkerState(w.state))}</span><span>GPU</span><span>${esc(gpu)}</span><span>VRAM</span><span>${esc(vram)} MB</span><span>CUDA</span><span>${c.cuda_available?"oui":"non"}</span><span>Heartbeat</span><span>${esc(w.last_seen_at||"-")}</span></div></div>`;
 }).join(""):'<div class="muted" style="margin-top:10px">Aucun assistant distribué enregistré.</div>';
}
function openIncidentLog(key){setView("logs");const tab=document.querySelector(`.tab[data-log="${key}"]`);if(tab)tab.click();else refreshLogs()}
async function acknowledgeIncident(id){try{const r=await protectedFetch("/api/incidents/ack",{method:"POST",headers:{"Content-Type":"application/json","X-EZS-Token":TOKEN},body:JSON.stringify({incident_id:id})});const d=await r.json();if(!r.ok)throw new Error(d.error||d.message||JSON.stringify(d));toast("Incident acquitté",true);await refresh()}catch(e){toast(String(e),false)}}
function renderIncidents(items){const rows=Array.isArray(items)?items:[];txt("incidentCount",`${rows.length} actif${rows.length===1?"":"s"}`);const el=$("incidentList");if(!el)return;el.innerHTML=rows.length?rows.map(i=>`<div class="incidentRow"><span class="incidentLevel ${esc(i.severity||"ERROR")}">${esc(i.severity||"ERROR")}</span><div><strong>${esc(i.code||"incident")}</strong> · ${esc(i.message||"")}<div class="muted">${esc(i.source||"-")} · ${i.acknowledged_at?"ACQUITTÉ":"NON ACQUITTÉ"}</div></div><div>${i.log_key?`<button data-incident-log="${esc(i.log_key)}">Logs</button>`:""} ${i.acknowledged_at?"✓":`<button data-incident-ack="${esc(i.id)}">Acquitter</button>`}</div></div>`).join(""):'<div class="muted">(aucun incident actif)</div>';el.querySelectorAll("[data-incident-ack]").forEach(b=>b.addEventListener("click",()=>acknowledgeIncident(b.dataset.incidentAck)));el.querySelectorAll("[data-incident-log]").forEach(b=>b.addEventListener("click",()=>openIncidentLog(b.dataset.incidentLog)))}
function renderSafety(payload){
 const safety=payload||{state:"ERROR",errors:1,warnings:0,issues:[{message:"État de supervision indisponible."}]};
 const state=String(safety.state||"ERROR").toUpperCase();
 const issues=Array.isArray(safety.issues)?safety.issues:[];
 const banner=$("safetyBanner");
 banner.className="safetyBanner "+(state==="ERROR"?"error":state==="WARNING"?"warning":"");
 txt("safetyTitle",state==="ERROR"?`ERREUR DÉTECTÉE — ${safety.errors??issues.length}`:state==="WARNING"?`ANOMALIE DÉTECTÉE — ${safety.warnings??issues.length}`:"Supervision processus : OK");
 txt("safetyDetail",issues.length?issues.slice(0,3).map(x=>x.message||x.code||"anomalie").join(" · "):"Aucune anomalie processus/queue et aucune erreur actionable depuis la dernière purge.");
 const btn=$("safetyLogs");
 if(btn)btn.dataset.log=(issues.find(x=>x.log_key)||{}).log_key||"control_center_error";
 renderIncidents(safety.incidents||[]);
 return state;
}

function renderStatus(s){
 analysisActive=!!s.analysis_active;
 const safetyState=renderSafety(s.safety);
 txt("updated",`${s.at} · snapshot ${s.snapshot_ms??'-'} ms · CC ${fmtMetric(s.control_center||{})}`);
 txt("globalState",safetyState==="ERROR"?"ERREUR":safetyState==="WARNING"?"ANOMALIE":analysisActive?"ANALYSE ACTIVE":"Système disponible");
 const globalBadge=$("globalState");globalBadge.className="globalBadge "+(safetyState==="ERROR"?"bad":safetyState==="WARNING"?"warn":analysisActive?"busy":"");
 const banner=$("analysisBanner");banner.textContent=analysisActive?"ANALYSE ACTIVE — stop/restart et déploiement bloqués":"Aucune analyse active";banner.className="banner "+(analysisActive?"active":"");
 dot($("gpuDot"),!analysisActive,analysisActive);txt("gpuState",analysisActive?"OCCUPÉ":"LIBRE");
 const svc=s.service||{};dot($("serviceDot"),!!svc.running);txt("serviceState",svc.running?"ACTIF":"ARRÊTÉ");txt("serviceTarget",svc.target?String(svc.target).toUpperCase():"-");txt("serviceMeta",`pid=${svc.pid??'-'} · state=${svc.state??'-'} · heartbeat=${svc.heartbeat??'-'} · ${fmtMetric(svc)}`);$("serviceStart").disabled=busy||!!svc.running;$("serviceStop").disabled=busy||!svc.running;
 const d=s.dev,ds=d.server,dc=d.caddy;const devHealthy=!!(ds.process_alive&&ds.http_alive&&dc.process_alive&&dc.http_alive);devFailures=devHealthy?0:devFailures+1;const devShown=devHealthy||devFailures<3;dot($("devDot"),devShown,!devHealthy);txt("devState",devHealthy?"EN LIGNE":(devFailures<3?"VÉRIFICATION":"HORS LIGNE"));txt("devRoot",ds.root);txt("devEnv",ds.app_env);txt("devBackend",`:${ds.backend_port} · ${fmtProc(ds)}`);txt("devCaddy",`:${dc.public_port} · ${fmtProc(dc)}`);txt("devTransport",d.transport);txt("devPython",d.analysis_python);txt("devOwnership",fmtOwnership(ds.ownership));
 const p=s.prod,pl=p.lifecycle,pb=pl.backend,pg=pl.gateway,pc=pl.caddy;const prodHealthy=!!pl.online;prodFailures=prodHealthy?0:prodFailures+1;const prodShown=prodHealthy||prodFailures<3;dot($("prodDot"),prodShown,!prodHealthy);txt("prodState",prodHealthy?"EN LIGNE":(prodFailures<3?"VÉRIFICATION":"CHAÎNE INCOMPLÈTE"));txt("prodRoot",pb.root);txt("prodBackend",`:${pb.backend_port} · ${fmtProc(pb)}`);txt("prodGateway",`:${pg.port} · pid ${pg.pid??'-'} · ${pg.process_alive?'PROCESSUS OK':'PROCESSUS ARRÊTÉ'} · ${pg.http_alive?'HTTP OK':'HTTP KO'} · ${pg.protocol??'-'} · propriété=${fmtOwnership(pg.ownership)}`);txt("prodCaddy",`:${pc.public_port} · ${fmtProc(pc)}`);txt("prodTransport",p.transport);txt("prodPython",p.analysis_python);txt("prodOwnership",fmtOwnership(pb.ownership));const mode=$("prodMode");mode.textContent=pl.mode==="maintenance"?"MAINTENANCE":pl.mode==="normal"?"NORMAL":String(pl.mode||"-").toUpperCase();mode.className="mode "+(pl.mode==="maintenance"?"maintenance":"");
 const l=s.lab||{},ls=l.server||{},lc=l.caddy||{};const labHealthy=!!(ls.process_alive&&ls.http_alive&&lc.process_alive&&lc.http_alive);labFailures=labHealthy?0:labFailures+1;const labShown=labHealthy||labFailures<3;dot($("labDot"),labShown,!labHealthy);txt("labState",labHealthy?"EN LIGNE":(labFailures<3?"VÉRIFICATION":"HORS LIGNE"));txt("labRoot",ls.root??l.root);txt("labEnv",ls.app_env);txt("labBackend",`:${ls.backend_port??8701} · ${fmtProc(ls)}`);txt("labCaddy",`:${lc.public_port??8702} · ${fmtProc(lc)}`);txt("labTransport",l.transport);txt("labPython",l.analysis_python);txt("labOwnership",fmtOwnership(ls.ownership));renderAssistantWorkers(l.workers||{});
 syncActionButtons();
}
function renderJobs(payload){
 const jobs=(payload&&payload.jobs)||[],running=payload?.running??0,waiting=payload?.waiting??0;
 txt("jobsMeta",payload&&payload.ok?`${payload.count??jobs.length} job(s) · ${running} running · ${waiting} waiting · IA canonique ${payload.ai_canonical_count??0} · exécution séquentielle${payload.queue_errors?.lab_ai?" · IA indisponible":""}`:"Erreur");
 $("jobsBody").innerHTML=jobs.length?jobs.map(j=>{const state=String(j.state||"unknown").toLowerCase(),target=String(j.target||"-").toLowerCase();const job=(j.job_id&&j.job_id!=="-")?`#${esc(j.job_id)}${j.source==="lab_canonical_ai"?" · IA":""}`:"-";const song=j.song_title?`${esc(j.song_title)}${j.song_id?` (#${esc(j.song_id)})`:""}`:(j.song_id?`#${esc(j.song_id)}`:"-");const date=j.timestamp||((state==="waiting"&&j.queue_position)?`position ${j.queue_position}`:"-");return `<tr><td><strong>${job}</strong></td><td><span class="job-target ${esc(target)}">${esc(target.toUpperCase())}</span></td><td>${song}</td><td>${esc(j.kind||"-")}</td><td><span class="job-state ${esc(state)}">${esc(state.toUpperCase())}</span></td><td>${esc(date)}</td><td>${esc(j.analysis_returncode??"-")}</td><td>${esc(j.finalize_status||"-")}</td><td>${j.error?esc(j.error):"-"}</td></tr>`}).join(""):'<tr><td colspan="9">Aucun job récent.</td></tr>';
}
async function refreshJobs(){if(jobsRefreshInFlight)return;jobsRefreshInFlight=true;try{renderJobs(await getJSON("/api/jobs"))}catch(e){txt("jobsMeta","Erreur de lecture")}finally{jobsRefreshInFlight=false}}
async function refreshLogs(){
 try{
  if(currentLog==="assistant_xps"||currentLog==="assistant_xps_error"){
   const stream=currentLog==="assistant_xps"?"stdout":"stderr";
   const payload=await getJSON(`/api/assistant/logs?stream=${stream}`);
   const lines=payload.lines||[];
   $("logText").textContent=lines.length?lines.join("\n"):"(vide)";
   return;
  }
  if(currentLog==="deployments"){
   const history=await getJSON("/api/deployment/history");
   const items=history.items||[];
   if(!items.length){
    $("logText").textContent="Aucun déploiement journalisé.";
    return;
   }
   const lines=["HISTORIQUE DES DÉPLOIEMENTS",""];
   for(const x of items){
    const status=String(x.status||"inconnu").toUpperCase();
    const before=(x.previous_prod_commit||"").slice(0,12)||"-";
    const target=(x.target_commit||"").slice(0,12)||"-";
    const duration=x.duration_seconds!=null?` · ${x.duration_seconds} s`:"";
    lines.push(`${status} · ${x.id||"-"} · ${before} → ${target}${duration}`);
   }
   const latest=items[0];
   if(latest&&latest.id){
    lines.push("","","DERNIER DÉPLOIEMENT — JOURNAL DÉTAILLÉ","");
    try{
     const detail=await getJSON(`/api/deployment/detail?id=${encodeURIComponent(latest.id)}`);
     lines.push(JSON.stringify(detail,null,2));
    }catch(detailError){
     lines.push(`Impossible de charger le détail : ${detailError}`);
    }
   }
   $("logText").textContent=lines.join("\n");
   return;
  }
  const logs=await getJSON("/api/logs");
  const lines=logs[currentLog]||[];
  $("logText").textContent=lines.length?lines.join("\n"):"(vide)";
 }catch(e){
  $("logText").textContent=String(e);
 }
}
async function refresh(){
 if(refreshInFlight)return;
 refreshInFlight=true;
 try{
  renderStatus(await getJSON("/api/status"));
  if(currentView==="logs")await refreshLogs();
 }catch(e){
  txt("updated","Dernière actualisation impossible · "+new Date().toLocaleTimeString("fr-FR"));
  toast(String(e),false);
 }finally{refreshInFlight=false}
}
async function action(name){if(busy)return;busy=true;syncActionButtons();try{const r=await protectedFetch("/api/action",{method:"POST",headers:{"Content-Type":"application/json","X-EZS-Token":TOKEN},body:JSON.stringify({action:name})});const d=await r.json();toast(d.message||d.error||"OK",!!d.ok)}catch(e){toast(String(e),false)}finally{busy=false;await refresh()}}
async function assistantRuntimeAction(path,successMessage){
 if(busy)return;
 busy=true;
 syncActionButtons();
 try{
  const r=await protectedFetch(path,{method:"POST",headers:{"X-EZS-Token":TOKEN}});
  const data=await r.json();
  if(!r.ok)throw new Error(data.message||data.error||JSON.stringify(data));
  toast(successMessage,true);
 }catch(e){
  toast(String(e),false);
 }finally{
  busy=false;
  await refreshAssistantSupervision();
  await refresh();
  syncActionButtons();
 }
}
$("assistantStart").addEventListener("click",()=>assistantRuntimeAction("/api/assistant/supervision/start","Assistant XPS démarré"));
$("assistantStop").addEventListener("click",()=>assistantRuntimeAction("/api/assistant/supervision/stop","Assistant XPS arrêté"));
$("assistantDeploy").addEventListener("click",async()=>{
 if(busy)return;
 if(!confirm("Déployer la version validée de EZStudioLab_assistant vers le XPS ?"))return;
 busy=true;
 syncActionButtons();
 try{
  const r=await protectedFetch("/api/assistant/deployment/apply",{method:"POST",headers:{"X-EZS-Token":TOKEN}});
  const data=await r.json();
  if(!r.ok)throw new Error(data.message||data.error||JSON.stringify(data));
  toast(`Assistant déployé ${(data.commit||"").slice(0,12)}`,true);
 }catch(e){
  toast(String(e),false);
 }finally{
  busy=false;
  await refreshAssistantDeployment();
  await refreshAssistantSupervision();
  await refresh();
  syncActionButtons();
 }
});
document.querySelectorAll('button[data-action]').forEach(b=>b.addEventListener("click",()=>action(b.dataset.action)));$("serviceStart").addEventListener("click",()=>action("service-start-all"));$("serviceStop").addEventListener("click",()=>action("service-stop"));
$("clearLogs").addEventListener("click",async()=>{if(!confirm("Effacer physiquement et complètement tous les fichiers de logs gérés ? Cette action est irréversible."))return;await action("logs-clear");await refreshLogs()});
$("exportLogs").addEventListener("click",()=>{window.location.assign("/api/logs/export")});
document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>{
 document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));
 b.classList.add("active");
 currentLog=b.dataset.log;
 $("clearLogs").disabled=false;
 $("clearLogs").title="";
 refreshLogs();
}));

function renderDeployment(p){
 deployData=p;txt("deployDevSha",(p.dev_head||"").slice(0,12));txt("deployProdSha",(p.prod_head||"").slice(0,12));txt("deployDevMeta",`${p.dev_branch} · ${p.dev_clean?"CLEAN":"DIRTY"} · ${p.dev_pushed?"PUSHED":"NOT PUSHED"}`);txt("deployProdMeta",`${p.prod_branch} · ${p.prod_clean?"CLEAN":"DIRTY"} · ${p.prod_online?"ONLINE":"OFFLINE"}`);
 const dec=$("deployDecision");
 if(p.up_to_date){
  dec.textContent="À JOUR";
  dec.className="deployDecision idle";
  txt("deployReasons","DEV et PROD pointent sur le même commit. Aucun déploiement à effectuer.");
 }else{
  dec.textContent=p.ok?"DÉPLOIEMENT POSSIBLE":"DÉPLOIEMENT BLOQUÉ";
  dec.className="deployDecision "+(p.ok?"ok":"bad");
  txt("deployReasons",p.reasons&&p.reasons.length?p.reasons.join(" · "):"Tous les garde-fous sont satisfaits.");
 }
 const checks=[["DEV propre",p.dev_clean],["PROD propre",p.prod_clean],["DEV poussé",p.dev_pushed],["Fast-forward",p.fast_forward],["Aucune analyse active",!p.analysis_active],["PROD online",p.prod_online],["Aucun chemin protégé",!(p.protected_changes||[]).length],["PHP PROD",!!p.php],["Composer",!!p.composer]];
 $("deployChecks").innerHTML=checks.map(([l,ok])=>`<div class="check ${ok?"ok":"bad"}">${ok?"✓":"✗"} ${esc(l)}</div>`).join("");
 txt("deployFiles",p.change_count);txt("deploySensitive",p.sensitive_change_count);txt("deployMigrations",p.doctrine_migration_count);txt("deployPhp",p.php);txt("deployComposer",p.composer);txt("deployTarget",`${(p.prod_head||"").slice(0,12)} → ${(p.target_commit||"").slice(0,12)}`);
 $("deployDiff").innerHTML=(p.changed_files||[]).map(x=>`<tr><td>${esc(x.status)}</td><td>${esc(x.zone)}</td><td>${esc(x.path)}</td><td class="${x.protected?"sensitive":""}">${x.protected?"PROTÉGÉ":"-"}</td><td class="${x.sensitive?"sensitive":""}">${x.sensitive?"SENSIBLE":"-"}</td></tr>`).join("")||'<tr><td colspan="5">Aucune différence.</td></tr>';syncActionButtons();
}
let deploymentRefreshRunning=false;
async function refreshDeployment(){
 if(deploymentRefreshRunning)return;
 deploymentRefreshRunning=true;
 const refreshBtn=$("deployRefresh");
 const previousLabel=refreshBtn.textContent;
 refreshBtn.disabled=true;
 refreshBtn.textContent="Analyse…";
 $("deployDecision").textContent="ANALYSE EN COURS…";
 $("deployDecision").className="deployDecision";
 txt("deployReasons","Préflight DEV → PROD en cours : Git, état des dépôts, runtime et garde-fous.");
 try{
  const p=await getJSON("/api/deployment/plan");
  renderDeployment(p);
  const h=await getJSON("/api/deployment/history");
  $("deployHistory").innerHTML=(h.items||[]).map(x=>{
   const status=String(x.status||"").toUpperCase();
   const subject=x.commit_subject||`Commit ${(x.target_commit||"").slice(0,12)}`;
   const author=x.commit_author||"Auteur inconnu";
   const commit=(x.target_commit||"").slice(0,12)||"-";
   const duration=x.duration_seconds!=null?` · ${x.duration_seconds} s`:"";
   return `<button data-deployment-id="${esc(x.id)}"><strong>${esc(status)}</strong> · ${esc(subject)}<br><span class="muted">${esc(author)} · ${esc(commit)}${esc(duration)}</span></button>`;
  }).join("")||'<div class="muted">Aucun déploiement journalisé.</div>';
  document.querySelectorAll("[data-deployment-id]").forEach(b=>b.addEventListener("click",()=>loadDeployment(b.dataset.deploymentId)));
  if(p.up_to_date)toast("DEV et PROD sont déjà à jour.",true);
  else toast(p.ok?"Préflight terminé : déploiement possible.":"Préflight terminé : déploiement bloqué.",p.ok);
 }catch(e){
  deployData={ok:false};
  $("deployDecision").textContent="DÉPLOIEMENT BLOQUÉ";
  $("deployDecision").className="deployDecision bad";
  txt("deployReasons",String(e));
 }finally{
  deploymentRefreshRunning=false;
  refreshBtn.disabled=false;
  refreshBtn.textContent=previousLabel;
  syncActionButtons();
 }
}
function renderDeployProgress(detail){
 const p=(detail&&detail.progress)||{};
 const events=Array.isArray(p.events)?p.events:[];
 const box=$("deployProgress");
 const status=String(p.status||((detail&&detail.result&&detail.result.ok)?"completed":((detail&&detail.failure&&detail.failure.ok===false)?"failed":"running")));
 box.className="deployConsole "+status;
 txt("deployProgressState",status==="completed"?"Terminé":status==="failed"?"Échec":status==="running"?"En cours…":"-");
 if(!events.length){
  box.textContent="Préparation du déploiement…";
  return;
 }
 box.textContent=events.map(e=>{
  const at=String(e.at||"").replace("T"," ").replace("+00:00","Z");
  const mark=e.status==="completed"?"✓":e.status==="failed"?"✗":"…";
  return `${at}  ${mark}  ${e.message||e.step||""}`;
 }).join("\n");
 box.scrollTop=box.scrollHeight;
}
async function pollDeployProgress(targetCommit){
 try{
  const h=await getJSON("/api/deployment/history");
  const items=h.items||[];
  const item=items.find(x=>String(x.target_commit||"")===String(targetCommit||""))||items[0];
  if(!item)return;
  const d=await getJSON(`/api/deployment/detail?id=${encodeURIComponent(item.id)}`);
  renderDeployProgress(d);
 }catch(e){
  txt("deployProgressState","Lecture de progression indisponible");
 }
}
async function loadDeployment(id){try{const d=await getJSON(`/api/deployment/detail?id=${encodeURIComponent(id)}`);$("deployLog").textContent=JSON.stringify(d,null,2);renderDeployProgress(d)}catch(e){$("deployLog").textContent=String(e)}}
$("deployRefresh").addEventListener("click",refreshDeployment);
function openDeploymentModal(fresh){
 return new Promise(resolve=>{
  const backdrop=$("deployModalBackdrop");
  txt("deployModalCommit",`${(fresh.prod_head||"").slice(0,12)} → ${(fresh.target_commit||"").slice(0,12)}`);
  txt("deployModalFiles",String(fresh.change_count ?? 0));
  txt("deployModalMigrations",String(fresh.doctrine_migration_count ?? 0));
  txt("deployModalSensitive",String(fresh.sensitive_change_count ?? 0));
  let settled=false;
  const finish=(value)=>{
   if(settled)return;
   settled=true;
   backdrop.classList.remove("show");
   document.removeEventListener("keydown",onKey);
   $("deployModalCancel").onclick=null;
   $("deployModalConfirm").onclick=null;
   backdrop.onclick=null;
   resolve(value);
  };
  const onKey=(e)=>{if(e.key==="Escape")finish(false)};
  $("deployModalCancel").onclick=()=>finish(false);
  $("deployModalConfirm").onclick=()=>finish(true);
  backdrop.onclick=(e)=>{if(e.target===backdrop)finish(false)};
  document.addEventListener("keydown",onKey);
  backdrop.classList.add("show");
  $("deployModalConfirm").focus();
 });
}

$("deployApply").addEventListener("click",async()=>{
 if(busy)return;
 busy=true;
 syncActionButtons();
 let progressTimer=null;
 try{
  const fresh=await getJSON("/api/deployment/plan");
  renderDeployment(fresh);
  if(fresh.up_to_date)throw new Error("Aucun déploiement à effectuer : DEV et PROD sont déjà à jour.");
  if(!fresh.ok)throw new Error("Préflight bloquant.");
  const confirmed=await openDeploymentModal(fresh);
  if(!confirmed)return;
  txt("deployProgressState","Démarrage…");
  $("deployProgress").className="deployConsole running";
  $("deployProgress").textContent="Initialisation du déploiement…";
  await pollDeployProgress(fresh.target_commit);
  progressTimer=setInterval(()=>pollDeployProgress(fresh.target_commit),800);
  const r=await protectedFetch("/api/deployment/apply",{method:"POST",headers:{"Content-Type":"application/json","X-EZS-Token":TOKEN},body:JSON.stringify({confirm_commit:fresh.target_commit})});
  const data=await r.json();
  await pollDeployProgress(fresh.target_commit);
  if(!r.ok)throw new Error(data.message||data.error||JSON.stringify(data));
  toast(`Déploiement ${data.status}: ${(data.target_commit||"").slice(0,12)}`,true);
  await refreshDeployment();
  await refresh();
 }catch(e){
  toast(String(e),false);
  await refreshDeployment();
 }finally{
  if(progressTimer)clearInterval(progressTimer);
  busy=false;
  syncActionButtons();
 }
});

$("safetyLogs").addEventListener("click",()=>{
 const key=$("safetyLogs").dataset.log||"control_center_error";
 setView("logs");
 const tab=document.querySelector(`.tab[data-log="${key}"]`);
 if(tab)tab.click();else refreshLogs();
});
$("headerRefresh").addEventListener("click",async()=>{await refresh();await refreshJobs();await refreshAssistantDeployment();await refreshAssistantSupervision();if(currentView==="deployment")await refreshDeployment()});
// R27A: foreground-only polling, with immediate refresh on return.
function refreshVisibleInfrastructure(){
 if(document.hidden)return;
 refresh();
 if(currentView==="infrastructure")refreshAssistantSupervision();
}
document.addEventListener("visibilitychange",()=>{
 if(!document.hidden){refreshVisibleInfrastructure();refreshJobs();}
});
refresh();refreshJobs();refreshAssistantDeployment();refreshAssistantSupervision();
setInterval(refreshVisibleInfrastructure,5000);
setInterval(()=>{if(!document.hidden)refreshJobs()},5000);
setInterval(()=>{if(!document.hidden && currentView!=="infrastructure")refreshAssistantSupervision()},10000);
</script>
</body></html>'''


def _load_or_create_ui_token(runtime: Path) -> str:
    runtime.mkdir(parents=True, exist_ok=True)
    token_path = runtime / "control-center-ui.token"
    try:
        current = token_path.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError):
        current = ""
    if (
        len(current) >= 32
        and all(ch.isalnum() or ch in "-_" for ch in current)
    ):
        return current

    token = secrets.token_urlsafe(32)
    tmp = token_path.with_suffix(".token.tmp")
    tmp.write_text(token + "\n", encoding="ascii")
    tmp.replace(token_path)
    return token


def make_handler(center: ControlCenter, token: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "EZSControlCenter/1.0"

        def log_message(self, format: str, *args) -> None:
            return

        def _json(self, payload, code: int = 200) -> None:
            data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
            try:
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (
                BrokenPipeError,
                ConnectionAbortedError,
                ConnectionResetError,
            ):
                return

        def _send_log_export(self) -> None:
            try:
                archive = center.log_tools.export_zip()
                data = archive.read_bytes()
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header(
                    "Content-Disposition",
                    f'attachment; filename="{archive.name}"',
                )
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except (
                BrokenPipeError,
                ConnectionAbortedError,
                ConnectionResetError,
            ):
                return
            except Exception as exc:
                self._json({"ok": False, "error": str(exc)}, 500)

        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            path = parsed.path
            if path == "/":
                body = (
                    HTML.replace("__TOKEN__", token)
                    .replace("__ORCH_VERSION__", VERSION)
                    .replace("__DEV_VERSION__", DEV_VERSION)
                    .replace("__LAB_VERSION__", LAB_VERSION)
                    .replace("__ASSISTANT_VERSION__", ASSISTANT_VERSION)
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            if path == "/api/status":
                try:
                    self._json(center.snapshot())
                except Exception as exc:
                    self._json({"ok": False, "error": str(exc)}, 500)
                return
            if path == "/api/jobs":
                self._json(center.jobs())
                return
            if path == "/api/logs":
                self._json(center.logs())
                return
            if path == "/api/logs/export":
                self._send_log_export()
                return
            if path == "/api/assistant/supervision/status":
                self._json(center.assistant_supervision_status())
                return
            if path == "/api/assistant/logs":
                try:
                    stream = str((parse_qs(parsed.query).get("stream") or ["stdout"])[0])
                    self._json(center.assistant_logs(stream))
                except ValueError as exc:
                    self._json({"ok": False, "error": str(exc)}, 400)
                except Exception as exc:
                    self._json({"ok": False, "error": str(exc)}, 500)
                return
            if path == "/api/assistant/deployment/status":
                self._json(center.assistant_deployment_status())
                return
            if path == "/api/deployment/plan":
                try:
                    self._json(center.deployment_plan())
                except Exception as exc:
                    self._json({"ok": False, "error": str(exc)}, 500)
                return
            if path == "/api/deployment/history":
                self._json({"ok": True, "items": center.deployment_history()})
                return
            if path == "/api/deployment/detail":
                try:
                    deployment_id = str((parse_qs(parsed.query).get("id") or [""])[0])
                    self._json(center.deployment_detail(deployment_id))
                except FileNotFoundError as exc:
                    self._json({"ok": False, "error": str(exc)}, 404)
                except Exception as exc:
                    self._json({"ok": False, "error": str(exc)}, 400)
                return
            self._json({"ok": False, "error": "not_found"}, 404)

        def do_POST(self) -> None:
            path = urlparse(self.path).path

            # Backward-compatible read-only export for tabs opened before
            # this release. Export does not mutate application state.
            if path == "/api/logs/export":
                self._send_log_export()
                return

            if self.headers.get("X-EZS-Token") != token:
                self._json({"ok": False, "error": "forbidden"}, 403)
                return

            if path == "/api/incidents/ack":
                try:
                    length = min(
                        int(self.headers.get("Content-Length", "0")),
                        4096,
                    )
                    payload = json.loads(
                        self.rfile.read(length).decode("utf-8")
                    )
                    self._json(
                        center.acknowledge_incident(
                            str(payload.get("incident_id") or "")
                        )
                    )
                except KeyError as exc:
                    self._json(
                        {"ok": False, "error": str(exc)},
                        404,
                    )
                except Exception as exc:
                    self._json(
                        {"ok": False, "error": str(exc)},
                        400,
                    )
                return

            if path == "/api/assistant/supervision/start":
                try:
                    self._json(center.assistant_start())
                except Exception as exc:
                    self._json({"ok": False, "message": str(exc)}, 500)
                return

            if path == "/api/assistant/supervision/stop":
                try:
                    self._json(center.assistant_stop())
                except Exception as exc:
                    self._json({"ok": False, "message": str(exc)}, 500)
                return

            if path == "/api/assistant/deployment/apply":
                try:
                    self._json(center.assistant_deployment_apply())
                except Exception as exc:
                    self._json({"ok": False, "message": str(exc)}, 500)
                return

            if path == "/api/deployment/apply":
                try:
                    length = min(int(self.headers.get("Content-Length", "0")), 4096)
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    commit = str(payload.get("confirm_commit") or "").strip()
                    if not commit:
                        self._json({"ok": False, "message": "confirm_commit_required"}, 400)
                        return
                    self._json(center.deployment_apply(commit))
                except Exception as exc:
                    self._json({"ok": False, "message": str(exc)}, 500)
                return

            if path != "/api/action":
                self._json({"ok": False, "error": "not_found"}, 404)
                return

            try:
                length = min(int(self.headers.get("Content-Length", "0")), 4096)
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
                self._json(center.action(str(payload.get("action", ""))))
            except ValueError as exc:
                self._json({"ok": False, "message": str(exc)}, 400)
            except Exception as exc:
                self._json({"ok": False, "message": str(exc)}, 500)

    return Handler


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="EZS Orchestrator V1.0"
    )
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not (1024 <= args.port <= 65535):
        raise SystemExit(
            "port must be between 1024 and 65535"
        )

    config = load_runtime_config()
    singleton = ControlCenterSingleton(
        config.orchestrator_root / "runtime"
    )
    try:
        singleton.acquire(args.port)
    except ControlCenterSingletonBusy as exc:
        print(
            f"CONTROL_CENTER_ALREADY_RUNNING: {exc}",
            file=sys.stderr,
        )
        return 3

    server = None
    try:
        center = ControlCenter()
        token = _load_or_create_ui_token(
            config.orchestrator_root / "runtime"
        )
        server = ThreadingHTTPServer(
            (HOST, args.port),
            make_handler(center, token),
        )
        url = f"http://{HOST}:{args.port}/"
        print(
            f"EZS_ORCHESTRATOR_V1_0 {url}",
            flush=True,
        )
        print(
            "Views: Infrastructure | Queues & Jobs | Deployment",
            flush=True,
        )
        if not args.no_browser:
            threading.Timer(
                0.6,
                lambda: webbrowser.open(url),
            ).start()
        try:
            server.serve_forever(poll_interval=0.5)
        except KeyboardInterrupt:
            pass
        return 0
    finally:
        if server is not None:
            server.server_close()
        singleton.release()

if __name__ == "__main__":
    raise SystemExit(main())
