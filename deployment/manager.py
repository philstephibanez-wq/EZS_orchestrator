from __future__ import annotations

import json
import os
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from config.loader import RuntimeConfig
from contracts.target import Target
from prod_lifecycle.manager import ProdLifecycleManager
from runtime_guard.activity import analysis_execution_active


PROTECTED_PATHS = (
    ".env.local",
    "data",
    "var/storage",
    "var/runtime",
    "var/log",
    "var/cache",
    ".venv",
    ".venv-py313",
)


@dataclass(frozen=True, slots=True)
class DeploymentPreflight:
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
    protected_paths_untracked: bool
    ready: bool

    def as_dict(self) -> dict:
        return asdict(self)


class DeploymentManager:
    """Guarded CODE-only deployment from physical DEV to physical PROD.

    The only code transfer mechanism is Git. No recursive copy/sync command is
    used or permitted. Target-owned DATA/runtime remain physically separate.
    """

    def __init__(self, config: RuntimeConfig, prod: ProdLifecycleManager | None = None) -> None:
        self.config = config
        self.prod = prod or ProdLifecycleManager(config)
        self.runtime_root = config.orchestrator_root / "runtime" / "deployment"
        self.log_root = config.orchestrator_root / "logs" / "deployment"
        self.runtime_root.mkdir(parents=True, exist_ok=True)
        self.log_root.mkdir(parents=True, exist_ok=True)

    def _assert_topology(self) -> None:
        dev = self.config.dev.root.resolve()
        prod = self.config.prod.root.resolve()
        if dev == prod:
            raise RuntimeError("deploy_refused:dev_prod_root_collision")
        if str(dev).lower() != r"h:\ezscore_dev":
            raise RuntimeError(f"deploy_refused:unexpected_dev_root:{dev}")
        if str(prod).lower() != r"h:\ezscore":
            raise RuntimeError(f"deploy_refused:unexpected_prod_root:{prod}")

    def _run(
        self,
        cwd: Path,
        args: list[str],
        *,
        timeout: float = 120.0,
        check: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        proc = subprocess.run(
            args,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            shell=False,
        )
        if check and proc.returncode != 0:
            detail = (proc.stderr or proc.stdout or "").strip()
            raise RuntimeError(
                f"command_failed rc={proc.returncode} cwd={cwd} cmd={' '.join(args)} detail={detail[:1000]}"
            )
        return proc

    def _git(self, cwd: Path, *args: str, timeout: float = 120.0, check: bool = True) -> str:
        proc = self._run(cwd, ["git", *args], timeout=timeout, check=check)
        return (proc.stdout or "").strip()

    def _clean(self, root: Path) -> bool:
        return self._git(root, "status", "--porcelain=v1", "-uall") == ""

    def _branch(self, root: Path) -> str:
        return self._git(root, "branch", "--show-current")

    def _head(self, root: Path, ref: str = "HEAD") -> str:
        return self._git(root, "rev-parse", ref)

    def _assert_protected_paths_not_tracked(self, root: Path) -> None:
        tracked: list[str] = []
        for path in PROTECTED_PATHS:
            out = self._git(root, "ls-files", "--", path)
            if out:
                tracked.extend(line for line in out.splitlines() if line.strip())
        if tracked:
            raise RuntimeError(
                "deploy_refused:protected_paths_tracked:" + ",".join(tracked[:20])
            )

    def preflight(self, *, fetch: bool = True) -> DeploymentPreflight:
        self._assert_topology()
        dev = self.config.dev.root
        prod = self.config.prod.root

        if analysis_execution_active(self.config.orchestrator_root / "runtime"):
            raise RuntimeError("deploy_refused:analysis_execution_active")

        if fetch:
            self._git(dev, "fetch", "--prune", "origin", "master", timeout=180)
            self._git(prod, "fetch", "--prune", "origin", "master", timeout=180)

        dev_branch = self._branch(dev)
        prod_branch = self._branch(prod)
        if dev_branch != "master":
            raise RuntimeError(f"deploy_refused:dev_branch:{dev_branch}")
        if prod_branch != "master":
            raise RuntimeError(f"deploy_refused:prod_branch:{prod_branch}")

        self._assert_protected_paths_not_tracked(dev)
        self._assert_protected_paths_not_tracked(prod)

        dev_head = self._head(dev)
        prod_head = self._head(prod)
        origin_master = self._head(dev, "origin/master")
        dev_clean = self._clean(dev)
        prod_clean = self._clean(prod)
        dev_pushed = dev_head == origin_master

        ff = self._run(
            prod,
            ["git", "merge-base", "--is-ancestor", prod_head, dev_head],
            check=False,
        ).returncode == 0

        ready = bool(
            dev_clean
            and prod_clean
            and dev_pushed
            and ff
            and dev_branch == "master"
            and prod_branch == "master"
        )

        return DeploymentPreflight(
            dev_root=str(dev),
            prod_root=str(prod),
            dev_branch=dev_branch,
            prod_branch=prod_branch,
            dev_head=dev_head,
            prod_head=prod_head,
            origin_master=origin_master,
            dev_clean=dev_clean,
            prod_clean=prod_clean,
            dev_pushed=dev_pushed,
            fast_forward=ff,
            protected_paths_untracked=True,
            ready=ready,
        )

    def _write_last(self, payload: dict) -> None:
        path = self.runtime_root / "last.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        os.replace(tmp, path)

    def _append_log(self, log_path: Path, message: str) -> None:
        stamp = datetime.now(timezone.utc).isoformat()
        with log_path.open("a", encoding="utf-8") as fh:
            fh.write(f"{stamp} {message}\n")

    def deploy(self, *, expected_commit: str, confirmed: bool) -> dict:
        if not confirmed:
            raise RuntimeError("deploy_refused:explicit_confirmation_required")

        lock = self.runtime_root / "deploy.lock"
        try:
            fd = os.open(lock, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
        except FileExistsError as exc:
            raise RuntimeError("deploy_refused:deployment_already_active") from exc
        else:
            os.close(fd)

        started = datetime.now(timezone.utc)
        log_path = self.log_root / f"deploy-{started.strftime('%Y%m%dT%H%M%S.%fZ')}.log"
        result: dict = {
            "schema": "ezs.deployment-result.v1",
            "started_at": started.isoformat(),
            "expected_commit": expected_commit,
            "status": "running",
            "log": str(log_path),
        }
        self._write_last(result)

        original_mode = "normal"
        try:
            pre = self.preflight(fetch=True)
            result["preflight"] = pre.as_dict()
            self._append_log(log_path, f"PREFLIGHT {json.dumps(pre.as_dict(), ensure_ascii=False)}")

            if not pre.ready:
                raise RuntimeError("deploy_refused:preflight_not_ready")
            if expected_commit != pre.dev_head:
                raise RuntimeError(
                    f"deploy_refused:commit_changed expected={expected_commit} actual={pre.dev_head}"
                )

            current_prod = self.prod.view()
            if not current_prod.online:
                raise RuntimeError("deploy_refused:prod_not_online")
            original_mode = current_prod.mode

            if pre.prod_head == pre.dev_head:
                result.update(
                    {
                        "status": "already_deployed",
                        "deployed_commit": pre.dev_head,
                        "finished_at": datetime.now(timezone.utc).isoformat(),
                    }
                )
                self._append_log(log_path, f"NOOP already deployed commit={pre.dev_head}")
                self._write_last(result)
                return result

            self._append_log(log_path, f"MAINTENANCE ON previous_mode={original_mode}")
            self.prod.set_maintenance(True)

            prod_root = self.config.prod.root
            self._append_log(log_path, f"GIT fast-forward {pre.prod_head} -> {pre.dev_head}")
            self._git(prod_root, "merge", "--ff-only", pre.dev_head, timeout=180)

            deployed_head = self._head(prod_root)
            if deployed_head != pre.dev_head:
                raise RuntimeError(
                    f"deploy_failed:prod_head_mismatch expected={pre.dev_head} actual={deployed_head}"
                )

            php = str(self.config.web_php_for(Target.PROD))
            console = prod_root / "bin" / "console"
            if console.is_file():
                self._append_log(log_path, "MIGRATIONS doctrine:migrations:migrate --no-interaction --env=prod")
                self._run(
                    prod_root,
                    [php, "bin/console", "doctrine:migrations:migrate", "--no-interaction", "--env=prod"],
                    timeout=300,
                )
                self._append_log(log_path, "CACHE clear --env=prod --no-debug")
                self._run(
                    prod_root,
                    [php, "bin/console", "cache:clear", "--env=prod", "--no-debug"],
                    timeout=180,
                )
            else:
                self._append_log(log_path, "MIGRATIONS skipped: bin/console absent")

            self._append_log(log_path, "PROD restart")
            post_restart = self.prod.restart()
            if not post_restart.online:
                raise RuntimeError("deploy_failed:prod_health_after_restart")

            if original_mode == "normal":
                self._append_log(log_path, "MAINTENANCE OFF")
                final = self.prod.set_maintenance(False)
            else:
                final = self.prod.set_maintenance(True)

            if not final.online:
                raise RuntimeError("deploy_failed:final_prod_health")
            final_head = self._head(prod_root)
            if final_head != pre.dev_head:
                raise RuntimeError(
                    f"deploy_failed:final_head_mismatch expected={pre.dev_head} actual={final_head}"
                )

            result.update(
                {
                    "status": "completed",
                    "deployed_commit": final_head,
                    "prod_mode": final.mode,
                    "prod_online": final.online,
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            self._append_log(log_path, f"SUCCESS commit={final_head} mode={final.mode}")
            self._write_last(result)
            return result
        except Exception as exc:
            result.update(
                {
                    "status": "failed",
                    "error": str(exc),
                    "finished_at": datetime.now(timezone.utc).isoformat(),
                }
            )
            self._append_log(log_path, f"FAILED {exc}")
            self._append_log(log_path, "SAFETY: PROD maintenance state is not automatically cleared after failure")
            self._write_last(result)
            raise
        finally:
            lock.unlink(missing_ok=True)

    def last_result(self) -> dict:
        path = self.runtime_root / "last.json"
        if not path.is_file():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return {}
