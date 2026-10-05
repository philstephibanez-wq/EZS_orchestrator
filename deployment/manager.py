from __future__ import annotations

import json
import os
import shutil
import sqlite3
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from config.loader import RuntimeConfig
from contracts.target import Target
from prod_lifecycle.manager import ProdLifecycleManager
from runtime_guard.activity import analysis_execution_active
from server_manager.process import clear_process_cache, pid_alive

PROTECTED_PREFIXES = (
    ".env.local", "data/", "var/storage/", "var/runtime/", "var/log/",
    "var/cache/", "logs/", ".venv/", ".venv-py313/",
)
SENSITIVE_PREFIXES = (
    "migrations/", "config/", "src/Entity/", "src/Service/",
    "composer.json", "composer.lock",
)

@dataclass(frozen=True, slots=True)
class DeploymentPlan:
    ok: bool
    reasons: tuple[str, ...]
    dev_root: str
    prod_root: str
    dev_branch: str
    prod_branch: str
    dev_head: str
    prod_head: str
    origin_master: str
    dev_clean: bool
    prod_clean: bool
    dev_pushed: bool
    fast_forward: bool
    analysis_active: bool
    prod_online: bool
    php: str | None
    composer: str | None
    changed_files: tuple[dict, ...]
    protected_changes: tuple[str, ...]
    sensitive_changes: tuple[str, ...]
    doctrine_migrations: tuple[str, ...]

    @property
    def target_commit(self) -> str:
        return self.dev_head

    def as_dict(self) -> dict:
        payload = asdict(self)
        payload["target_commit"] = self.target_commit
        payload["up_to_date"] = self.dev_head == self.prod_head
        payload["change_count"] = len(self.changed_files)
        payload["protected_change_count"] = len(self.protected_changes)
        payload["sensitive_change_count"] = len(self.sensitive_changes)
        payload["doctrine_migration_count"] = len(self.doctrine_migrations)
        payload["steps"] = [
            "QUIESCE_WORKER", "MAINTENANCE_ON", "BACKUP_DB", "GIT_FF_ONLY",
            "COMPOSER_INSTALL", "DOCTRINE_MIGRATIONS", "CACHE_CLEAR",
            "PROD_RESTART", "HEALTH_CHECK", "RESTORE_WORKER",
        ]
        return payload

class DeploymentManager:
    """Fail-closed DEV -> PROD deployer. Code via Git; PROD data stay in PROD."""

    def __init__(self, config: RuntimeConfig, prod: ProdLifecycleManager | None = None) -> None:
        self.config = config
        self.prod = prod or ProdLifecycleManager(config)
        self.history_root = config.orchestrator_root / "runtime" / "deployments"
        self.history_root.mkdir(parents=True, exist_ok=True)

    def _assert_topology(self) -> None:
        dev = str(self.config.dev.root.resolve()).lower()
        prod = str(self.config.prod.root.resolve()).lower()
        if dev != r"h:\ezscore_dev":
            raise RuntimeError(f"deploy_refused:unexpected_dev_root:{dev}")
        if prod != r"h:\ezscore":
            raise RuntimeError(f"deploy_refused:unexpected_prod_root:{prod}")
        if dev == prod:
            raise RuntimeError("deploy_refused:dev_prod_root_collision")

    @staticmethod
    def _windows_command_argv(argv: list[str]) -> list[str]:
        if not argv:
            return argv
        executable = str(argv[0])
        suffix = Path(executable).suffix.lower()
        if os.name == "nt" and suffix in {".bat", ".cmd"}:
            comspec = os.environ.get("COMSPEC") or shutil.which("cmd.exe") or r"C:\Windows\System32\cmd.exe"
            return [comspec, "/d", "/s", "/c", subprocess.list2cmdline(argv)]
        return argv

    @staticmethod
    def _run(
        cwd: Path,
        argv: list[str],
        *,
        timeout: float = 180.0,
        check: bool = True,
        env_overrides: dict[str, str] | None = None,
    ) -> subprocess.CompletedProcess[str]:
        effective_argv = DeploymentManager._windows_command_argv(argv)
        child_env = os.environ.copy()
        if env_overrides:
            child_env.update(env_overrides)
        proc = subprocess.run(
            effective_argv, cwd=str(cwd), stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding="utf-8", errors="replace", timeout=timeout, shell=False,
            env=child_env,
        )
        if check and proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(f"command_failed rc={proc.returncode} cwd={cwd} cmd={' '.join(effective_argv)} detail={detail[:2000]}")
        return proc

    def _git(self, cwd: Path, *args: str, timeout: float = 180.0) -> str:
        return (self._run(cwd, ["git", *args], timeout=timeout).stdout or "").strip()

    def _head(self, root: Path, ref: str = "HEAD") -> str:
        return self._git(root, "rev-parse", ref)

    def _clean(self, root: Path) -> bool:
        return not bool(self._git(root, "status", "--porcelain=v1", "-uall"))

    def _branch(self, root: Path) -> str:
        return self._git(root, "branch", "--show-current")

    @staticmethod
    def _norm(path: str) -> str:
        return path.replace("\\", "/").lstrip("./")

    @classmethod
    def _protected(cls, path: str) -> bool:
        p = cls._norm(path)
        return any(p == q.rstrip("/") or p.startswith(q) for q in PROTECTED_PREFIXES)

    @classmethod
    def _sensitive(cls, path: str) -> bool:
        p = cls._norm(path)
        return any(p == q.rstrip("/") or p.startswith(q) for q in SENSITIVE_PREFIXES)

    def _changed(self, prod_head: str, dev_head: str) -> tuple[dict, ...]:
        if prod_head == dev_head:
            return ()
        out = self._git(self.config.dev.root, "diff", "--name-status", prod_head, dev_head)
        rows = []
        for line in out.splitlines():
            if not line.strip():
                continue
            parts = line.split("\t")
            status = parts[0]
            path = self._norm(parts[-1])
            rows.append({
                "status": status,
                "path": path,
                "zone": path.split("/", 1)[0] if "/" in path else "(root)",
                "protected": self._protected(path),
                "sensitive": self._sensitive(path),
            })
        return tuple(rows)

    def _resolve_php(self) -> str | None:
        candidate = self.config.web_php_for(Target.PROD)
        if candidate != Path("php"):
            return str(candidate) if candidate.is_file() else None
        return shutil.which("php") or shutil.which("php.exe")

    @staticmethod
    def _resolve_composer() -> str | None:
        return shutil.which("composer") or shutil.which("composer.bat") or shutil.which("composer.cmd")

    def _service_running(self) -> bool:
        meta = self.config.orchestrator_root / "runtime" / "service" / "service.json"
        if not meta.is_file():
            return False
        try:
            data = json.loads(meta.read_text(encoding="utf-8-sig"))
            pid = int(data.get("pid") or 0)
        except Exception:
            return False
        clear_process_cache()
        return pid > 0 and pid_alive(pid)

    def _service_stop(self) -> None:
        proc = self._run(
            self.config.orchestrator_root,
            [sys.executable, "-m", "service.service_cli", "stop", "--wait-seconds", "30"],
            timeout=40, check=False,
        )
        if proc.returncode != 0:
            raise RuntimeError("deploy_failed:worker_quiesce:" + ((proc.stderr or proc.stdout or "").strip()[:1500]))

    def _service_start(self) -> None:
        proc = self._run(
            self.config.orchestrator_root,
            [sys.executable, "-m", "service.service_cli", "start", "--target", "all", "--poll-seconds", "2"],
            timeout=15, check=False,
        )
        if proc.returncode not in (0, 3):
            raise RuntimeError("deploy_failed:worker_restore:" + ((proc.stderr or proc.stdout or "").strip()[:1500]))

    def plan(self, *, fetch: bool = True) -> DeploymentPlan:
        self._assert_topology()
        dev, prod = self.config.dev.root, self.config.prod.root
        if fetch:
            self._git(dev, "fetch", "--prune", "origin", "master")
            self._git(prod, "fetch", "--prune", "origin", "master")

        dev_branch, prod_branch = self._branch(dev), self._branch(prod)
        dev_head, prod_head = self._head(dev), self._head(prod)
        origin_master = self._head(dev, "origin/master")
        dev_clean, prod_clean = self._clean(dev), self._clean(prod)
        dev_pushed = dev_head == origin_master
        ff = self._run(prod, ["git", "merge-base", "--is-ancestor", prod_head, dev_head], check=False).returncode == 0
        active = bool(analysis_execution_active(self.config.orchestrator_root / "runtime"))
        prod_online = bool(self.prod.view().online)
        php, composer = self._resolve_php(), self._resolve_composer()

        changed = self._changed(prod_head, dev_head)
        protected = tuple(x["path"] for x in changed if x["protected"])
        sensitive = tuple(x["path"] for x in changed if x["sensitive"])
        migrations = tuple(x["path"] for x in changed if x["path"].startswith("migrations/"))

        reasons = []
        if dev_branch != "master": reasons.append(f"dev_branch:{dev_branch}")
        if prod_branch != "master": reasons.append(f"prod_branch:{prod_branch}")
        if not dev_clean: reasons.append("dev_dirty")
        if not prod_clean: reasons.append("prod_dirty")
        if not dev_pushed: reasons.append("dev_not_pushed")
        if not ff: reasons.append("prod_not_ancestor_of_dev")
        if dev_head == prod_head: reasons.append("already_up_to_date")
        if active: reasons.append("analysis_execution_active")
        if not prod_online: reasons.append("prod_not_online")
        if protected: reasons.append("protected_paths_changed")
        if php is None: reasons.append("prod_php_not_resolved")
        if composer is None: reasons.append("composer_not_resolved")

        return DeploymentPlan(
            ok=not reasons, reasons=tuple(reasons),
            dev_root=str(dev), prod_root=str(prod),
            dev_branch=dev_branch, prod_branch=prod_branch,
            dev_head=dev_head, prod_head=prod_head, origin_master=origin_master,
            dev_clean=dev_clean, prod_clean=prod_clean, dev_pushed=dev_pushed,
            fast_forward=ff, analysis_active=active, prod_online=prod_online,
            php=php, composer=composer,
            changed_files=changed, protected_changes=protected,
            sensitive_changes=sensitive, doctrine_migrations=migrations,
        )

    @staticmethod
    def _write_json(path: Path, payload: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(path.suffix + ".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8")
        os.replace(tmp, path)

    @staticmethod
    def _read_json(path: Path) -> dict:
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return {}

    def _progress(self, deployment_dir: Path, step: str, status: str, message: str) -> None:
        path = deployment_dir / "progress.json"
        payload = self._read_json(path)
        events = payload.get("events") if isinstance(payload.get("events"), list) else []
        event = {
            "at": datetime.now(timezone.utc).isoformat(),
            "step": step,
            "status": status,
            "message": message,
        }
        events.append(event)
        self._write_json(path, {
            "schema": "ezs.deployment-progress.v1",
            "status": status,
            "current_step": step,
            "message": message,
            "events": events[-200:],
        })

    def _step(
        self,
        deployment_dir: Path,
        step_id: str,
        cwd: Path,
        argv: list[str],
        *,
        timeout: float,
        env_overrides: dict[str, str] | None = None,
    ) -> None:
        started = datetime.now(timezone.utc)
        self._progress(deployment_dir, step_id, "running", f"{step_id}…")
        proc = self._run(
            cwd,
            argv,
            timeout=timeout,
            check=False,
            env_overrides=env_overrides,
        )
        finished = datetime.now(timezone.utc)
        payload = {
            "schema": "ezs.deployment-step.v1", "id": step_id,
            "started_at": started.isoformat(), "finished_at": finished.isoformat(),
            "duration_seconds": (finished - started).total_seconds(),
            "cwd": str(cwd), "argv": argv, "returncode": proc.returncode,
            "environment": dict(env_overrides or {}),
            "stdout": proc.stdout or "", "stderr": proc.stderr or "",
        }
        self._write_json(deployment_dir / "steps" / f"{step_id}.json", payload)
        if proc.returncode != 0:
            self._progress(deployment_dir, step_id, "failed", f"{step_id} échoué (rc={proc.returncode}).")
            raise RuntimeError(f"deploy_failed:{step_id}:rc={proc.returncode}")
        self._progress(deployment_dir, step_id, "completed", f"{step_id} terminé.")

    def _backup_db(self, deployment_dir: Path) -> str | None:
        source = self.config.prod.root / "data" / "ezscore_v1.sqlite"
        if not source.is_file():
            return None
        backup = deployment_dir / "backup" / "ezscore_v1.sqlite"
        backup.parent.mkdir(parents=True, exist_ok=True)
        src, dst = sqlite3.connect(str(source)), sqlite3.connect(str(backup))
        try:
            src.backup(dst)
        finally:
            dst.close()
            src.close()
        return str(backup)

    def apply(self, confirmed_commit: str) -> dict:
        if not confirmed_commit:
            raise RuntimeError("deploy_refused:confirmation_commit_required")

        lock = self.history_root / ".deploy.lock"
        try:
            fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError as exc:
            raise RuntimeError("deploy_refused:deployment_already_active") from exc
        else:
            os.close(fd)

        started = datetime.now(timezone.utc)
        deployment_dir = None
        worker_was_running = False
        original_mode = "normal"
        plan = None

        try:
            plan = self.plan(fetch=True)
            if not plan.ok:
                raise RuntimeError("deploy_refused:preflight:" + ",".join(plan.reasons))
            if confirmed_commit != plan.target_commit:
                raise RuntimeError(f"deploy_refused:commit_changed:expected={confirmed_commit}:actual={plan.target_commit}")

            deployment_id = started.strftime("%Y%m%dT%H%M%S.%fZ") + "_" + plan.target_commit[:12]
            deployment_dir = self.history_root / deployment_id
            deployment_dir.mkdir(parents=True, exist_ok=False)
            self._write_json(deployment_dir / "plan.json", plan.as_dict())
            self._progress(deployment_dir, "preflight", "running", "Préflight validé. Préparation du déploiement.")

            current_prod = self.prod.view()
            original_mode = current_prod.mode
            worker_was_running = self._service_running()

            if worker_was_running:
                self._progress(deployment_dir, "worker-stop", "running", "Arrêt du service permanent.")
                self._service_stop()
                self._progress(deployment_dir, "worker-stop", "completed", "Service permanent arrêté.")

            if analysis_execution_active(self.config.orchestrator_root / "runtime"):
                raise RuntimeError("deploy_refused:analysis_became_active")

            self._progress(deployment_dir, "second-preflight", "running", "Revalidation des garde-fous.")
            second = self.plan(fetch=True)
            if not second.ok:
                raise RuntimeError("deploy_refused:second_preflight:" + ",".join(second.reasons))
            if second.target_commit != confirmed_commit:
                raise RuntimeError("deploy_refused:target_moved_after_confirmation")

            self._progress(deployment_dir, "maintenance-on", "running", "Passage de PROD en maintenance.")
            self.prod.set_maintenance(True)
            self._progress(deployment_dir, "maintenance-on", "completed", "PROD est en maintenance.")

            self._progress(deployment_dir, "backup-db", "running", "Sauvegarde de la base PROD.")
            backup_db = self._backup_db(deployment_dir)
            self._progress(deployment_dir, "backup-db", "completed", "Sauvegarde de la base PROD terminée.")
            prod_root = self.config.prod.root

            self._step(deployment_dir, "git-ff-only", prod_root, ["git", "merge", "--ff-only", confirmed_commit], timeout=180)
            if self._head(prod_root) != confirmed_commit:
                raise RuntimeError("deploy_failed:prod_head_after_git")

            assert second.composer is not None
            assert second.php is not None

            prod_command_env = {"APP_ENV": "prod", "APP_DEBUG": "0"}

            self._step(
                deployment_dir,
                "composer-install",
                prod_root,
                [second.composer, "install", "--no-dev", "--prefer-dist", "--no-interaction", "--optimize-autoloader"],
                timeout=600,
                env_overrides=prod_command_env,
            )
            self._step(
                deployment_dir,
                "doctrine-migrations",
                prod_root,
                [second.php, "bin/console", "doctrine:migrations:migrate", "--no-interaction", "--env=prod"],
                timeout=600,
                env_overrides=prod_command_env,
            )
            self._step(
                deployment_dir,
                "cache-clear",
                prod_root,
                [second.php, "bin/console", "cache:clear", "--env=prod", "--no-debug"],
                timeout=300,
                env_overrides=prod_command_env,
            )

            self._progress(deployment_dir, "prod-restart", "running", "Redémarrage de PROD.")
            restarted = self.prod.restart()
            if not restarted.online:
                raise RuntimeError("deploy_failed:prod_health_after_restart")

            self._progress(deployment_dir, "health-check", "completed", "PROD répond après redémarrage.")
            self._progress(deployment_dir, "maintenance-restore", "running", "Restauration du mode PROD.")
            final = self.prod.set_maintenance(False) if original_mode == "normal" else self.prod.set_maintenance(True)
            if not final.online:
                raise RuntimeError("deploy_failed:prod_final_health")
            if self._head(prod_root) != confirmed_commit:
                raise RuntimeError("deploy_failed:prod_final_head")

            if worker_was_running:
                self._progress(deployment_dir, "worker-restore", "running", "Redémarrage du service permanent.")
                self._service_start()
                self._progress(deployment_dir, "worker-restore", "completed", "Service permanent redémarré.")

            self._progress(deployment_dir, "completed", "completed", "Déploiement terminé avec succès.")
            finished = datetime.now(timezone.utc)
            result = {
                "schema": "ezs.deployment-result.v1", "ok": True, "status": "completed",
                "deployment_id": deployment_id,
                "started_at": started.isoformat(), "finished_at": finished.isoformat(),
                "duration_seconds": (finished - started).total_seconds(),
                "previous_prod_commit": plan.prod_head, "target_commit": confirmed_commit,
                "backup_db": backup_db, "prod_mode": final.mode,
                "prod_online": final.online, "worker_restored": worker_was_running,
            }
            self._write_json(deployment_dir / "result.json", result)
            return result

        except Exception as exc:
            if deployment_dir is not None:
                self._progress(deployment_dir, "failed", "failed", str(exc))
                self._write_json(deployment_dir / "failure.json", {
                    "schema": "ezs.deployment-failure.v1", "ok": False, "status": "failed",
                    "started_at": started.isoformat(), "finished_at": datetime.now(timezone.utc).isoformat(),
                    "previous_prod_commit": plan.prod_head if plan else None,
                    "target_commit": plan.target_commit if plan else confirmed_commit,
                    "error": str(exc),
                    "safety": "PROD maintenance is intentionally not cleared automatically after a deployment failure.",
                })
            raise
        finally:
            lock.unlink(missing_ok=True)

    def _commit_metadata(self, commit: str | None) -> dict:
        if not commit:
            return {}
        proc = self._run(
            self.config.prod.root,
            ["git", "show", "-s", "--format=%H%x1f%an%x1f%ae%x1f%aI%x1f%s", commit],
            timeout=30,
            check=False,
        )
        if proc.returncode != 0 or not (proc.stdout or "").strip():
            return {}
        parts = (proc.stdout or "").strip().split("\x1f", 4)
        if len(parts) != 5:
            return {}
        return {
            "commit": parts[0],
            "author_name": parts[1],
            "author_email": parts[2],
            "authored_at": parts[3],
            "subject": parts[4],
        }

    def history(self, limit: int = 30) -> list[dict]:
        rows = []
        if not self.history_root.is_dir():
            return rows
        for d in sorted((p for p in self.history_root.iterdir() if p.is_dir()), key=lambda p: p.name, reverse=True):
            plan = self._read_json(d / "plan.json")
            result = self._read_json(d / "result.json")
            failure = self._read_json(d / "failure.json")
            final = result or failure
            target_commit = final.get("target_commit") or plan.get("target_commit")
            commit_meta = self._commit_metadata(target_commit)
            rows.append({
                "id": d.name,
                "status": "completed" if result.get("ok") else ("failed" if failure else "in_progress"),
                "previous_prod_commit": final.get("previous_prod_commit") or plan.get("prod_head"),
                "target_commit": target_commit,
                "commit_subject": commit_meta.get("subject"),
                "commit_author": commit_meta.get("author_name"),
                "commit_authored_at": commit_meta.get("authored_at"),
                "duration_seconds": final.get("duration_seconds"),
                "error": final.get("error"),
                "backup_db": final.get("backup_db"),
            })
            if len(rows) >= limit:
                break
        return rows

    def detail(self, deployment_id: str) -> dict:
        if not deployment_id or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_.T" for c in deployment_id):
            raise ValueError("invalid_deployment_id")
        root = self.history_root.resolve()
        target = (root / deployment_id).resolve()
        if root not in target.parents or not target.is_dir():
            raise FileNotFoundError("deployment_not_found")
        steps = []
        step_root = target / "steps"
        if step_root.is_dir():
            for p in sorted(step_root.glob("*.json")):
                steps.append(self._read_json(p))
        return {
            "id": deployment_id,
            "plan": self._read_json(target / "plan.json"),
            "result": self._read_json(target / "result.json"),
            "failure": self._read_json(target / "failure.json"),
            "progress": self._read_json(target / "progress.json"),
            "steps": steps,
        }
