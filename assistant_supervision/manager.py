from __future__ import annotations

import base64
import json
import os
import subprocess
import threading
import time
from dataclasses import dataclass
from pathlib import Path


DEFAULT_NODE = "steph@192.168.1.81"
DEFAULT_REMOTE_ROOT = r"C:\EZStudioLab_assistant"
DEFAULT_REMOTE_RUNTIME = r"C:\EZStudioLab_assistant\runtime"


@dataclass(frozen=True)
class AssistantRemoteStatus:
    ok: bool
    state: str
    process_running: bool
    process_count: int
    profile_review_running: bool
    profile_review_count: int
    web_running: bool
    web_listener_count: int
    web_version: str | None
    deployed_commit: str | None
    node: str
    remote_root: str
    stdout_log: str
    stderr_log: str
    profile_stdout_log: str
    profile_stderr_log: str
    error: str | None

    def as_dict(self) -> dict:
        return {
            "ok": self.ok,
            "schema": "ezs.assistant-supervision.status.v1",
            "state": self.state,
            "process_running": self.process_running,
            "process_count": self.process_count,
            "profile_review_running": self.profile_review_running,
            "profile_review_count": self.profile_review_count,
            "web_running": self.web_running,
            "web_listener_count": self.web_listener_count,
            "web_version": self.web_version,
            "deployed_commit": self.deployed_commit,
            "node": self.node,
            "remote_root": self.remote_root,
            "stdout_log": self.stdout_log,
            "stderr_log": self.stderr_log,
            "profile_stdout_log": self.profile_stdout_log,
            "profile_stderr_log": self.profile_stderr_log,
            "error": self.error,
        }

class AssistantSupervisor:
    def __init__(
        self,
        node: str = DEFAULT_NODE,
        remote_root: str = DEFAULT_REMOTE_ROOT,
        cache_seconds: float = 4.0,
        remote_runtime: str = DEFAULT_REMOTE_RUNTIME,
    ) -> None:
        self.node = node
        self.remote_root = remote_root
        self.remote_runtime = remote_runtime
        self.log_root = remote_root + r"\logs"
        self.cache_seconds = float(cache_seconds)
        self._lock = threading.Lock()
        self._status_cache: tuple[float, dict] | None = None

    @staticmethod
    def _encoded(script: str) -> str:
        return base64.b64encode(script.encode("utf-16le")).decode("ascii")

    def _run_ps(
        self,
        script: str,
        timeout: int = 15,
        stdin_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if stdin_text is not None:
            raise ValueError("assistant_remote_ps_stdin_payload_not_supported")
        # Keep the SSH command line short. The status probe is intentionally
        # sizeable and can exceed the Windows command-line limit when sent as
        # PowerShell -EncodedCommand.
        return subprocess.run(
            [
                "ssh",
                self.node,
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-Command",
                "-",
            ],
            input=script,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

    def _run_remote_helper(
        self,
        command: str,
        timeout: int = 30,
        stdin_text: str | None = None,
    ) -> subprocess.CompletedProcess[str]:
        if command not in {"start", "stop"}:
            raise ValueError("assistant_remote_helper_command_invalid")
        helper = self.remote_runtime + r"\assistant-supervision.ps1"
        return subprocess.run(
            [
                "ssh",
                self.node,
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                helper,
                command,
            ],
            input=stdin_text,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
        )

    def _configured_token(self) -> str:
        runtime = str(os.getenv("EZSTUDIO_ANALYSIS_WORKER_TOKEN") or "").strip()
        if runtime:
            return runtime
        env_path = Path(r"H:\EZStudio_lab\.env.local")
        if not env_path.is_file():
            raise RuntimeError("assistant_analysis_token_env_missing")
        for raw in env_path.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            if key.strip() != "EZSTUDIO_ANALYSIS_WORKER_TOKEN":
                continue
            value = value.strip().strip('"').strip("'").strip()
            if value:
                return value
        raise RuntimeError("assistant_analysis_token_missing")

    def status(self, force: bool = False) -> dict:
        with self._lock:
            now = time.monotonic()
            if (
                not force
                and self._status_cache is not None
                and now - self._status_cache[0] < self.cache_seconds
            ):
                return dict(self._status_cache[1])

        script = f"""$ErrorActionPreference = 'Stop'
    $root = '{self.remote_root}'
    $stdoutPath = Join-Path $root 'logs\\assistant.out.log'
    $stderrPath = Join-Path $root 'logs\\assistant.err.log'
    $profileStdoutPath = Join-Path $root 'logs\\profile-review.out.log'
    $profileStderrPath = Join-Path $root 'logs\\profile-review.err.log'
    $versionPath = Join-Path $root 'VERSION'
    $webRuntime = Join-Path $root 'runtime\\web'
    $caddyPidPath = Join-Path $webRuntime 'caddy.pid'
    $phpPidPath = Join-Path $webRuntime 'php.pid'

    function Get-PortOwner([int]$Port) {{
        $listener = Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -eq $listener) {{ return $null }}
        return [int]$listener.OwningProcess
    }}

    function Test-AssistantPortOwner(
        [int]$Port,
        [string]$ExpectedName,
        [string]$PidPath
    ) {{
        $owner = Get-PortOwner $Port
        if ($null -eq $owner) {{ return $false }}

        $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$owner" -ErrorAction SilentlyContinue
        if ($null -eq $processInfo) {{ return $false }}
        if ([string]$processInfo.Name -ne $ExpectedName) {{ return $false }}

        $cmd = [string]$processInfo.CommandLine
        if (
            -not [string]::IsNullOrWhiteSpace($cmd) -and
            $cmd.IndexOf($root, [System.StringComparison]::OrdinalIgnoreCase) -ge 0
        ) {{
            return $true
        }}

        if (Test-Path -LiteralPath $PidPath -PathType Leaf) {{
            try {{ $persisted = [int](Get-Content -LiteralPath $PidPath -Raw) }}
            catch {{ return $false }}
            return $persisted -eq $owner
        }}

        return $false
    }}

    $owner8712 = Get-PortOwner 8712
    $owner8713 = Get-PortOwner 8713
    $assistant8712 = Test-AssistantPortOwner 8712 'caddy.exe' $caddyPidPath
    $assistant8713 = Test-AssistantPortOwner 8713 'php.exe' $phpPidPath

    $webPorts = @(
        if ($null -ne $owner8712) {{ 8712 }}
        if ($null -ne $owner8713) {{ 8713 }}
    )
    $webRunning = ($assistant8712 -and $assistant8713)
    $webForeign = (
        ($null -ne $owner8712 -and -not $assistant8712) -or
        ($null -ne $owner8713 -and -not $assistant8713)
    )
    $webVersion = $null
    if (Test-Path -LiteralPath $versionPath -PathType Leaf) {{
        $webVersion = (Get-Content -LiteralPath $versionPath -Raw).Trim()
    }}
    $distributedMatches = @(
        Get-CimInstance Win32_Process | Where-Object {{
            $_.CommandLine -and
            $_.CommandLine -like '*EZStudioLab_assistant*app*main.py*' -and
            $_.CommandLine -like '*distributed-watch*'
        }}
    )
    $profileMatches = @(
        Get-CimInstance Win32_Process | Where-Object {{
            $_.CommandLine -and
            $_.CommandLine -like '*EZStudioLab_assistant*app*main.py*' -and
            $_.CommandLine -like '*profile-review-auto-watch*'
        }}
    )
    $commit = $null
    if (Test-Path -LiteralPath (Join-Path $root '.git') -PathType Container) {{
        $commit = (& git -C $root rev-parse HEAD 2>$null)
        if ($LASTEXITCODE -eq 0 -and $null -ne $commit) {{
            $commit = ([string]$commit).Trim()
        }}
        else {{
            $commit = $null
        }}
    }}
    [pscustomobject]@{{
        process_count = [int]$distributedMatches.Count
        profile_review_count = [int]$profileMatches.Count
        web_running = [bool]$webRunning
        web_foreign = [bool]$webForeign
        web_listener_count = [int]$webPorts.Count
        web_version = $webVersion
        deployed_commit = $commit
        stdout_log = $stdoutPath
        stderr_log = $stderrPath
        profile_stdout_log = $profileStdoutPath
        profile_stderr_log = $profileStderrPath
    }} | ConvertTo-Json -Compress
    """
        try:
            completed = self._run_ps(script)
        except subprocess.TimeoutExpired:
            payload = self._error_status("ssh_timeout")
        except OSError as exc:
            payload = self._error_status(f"{type(exc).__name__}:{exc}"[:500])
        else:
            if completed.returncode != 0:
                error = (
                    completed.stderr.strip()
                    or completed.stdout.strip()
                    or f"ssh_rc={completed.returncode}"
                )
                payload = self._error_status(error[:500])
            else:
                try:
                    rows = [
                        line.strip()
                        for line in completed.stdout.splitlines()
                        if line.strip()
                    ]
                    raw = json.loads(rows[-1])
                    distributed_count = int(raw.get("process_count") or 0)
                    profile_count = int(raw.get("profile_review_count") or 0)
                    web_running = bool(raw.get("web_running"))
                    web_foreign = bool(raw.get("web_foreign"))
                    web_listener_count = int(raw.get("web_listener_count") or 0)
                    web_version = str(raw.get("web_version") or "").strip() or None
                    if web_foreign:
                        state = "FOREIGN"
                    elif (
                        distributed_count == 1
                        and profile_count == 1
                        and web_running
                        and web_listener_count == 2
                    ):
                        state = "RUNNING"
                    elif (
                        distributed_count == 0
                        and profile_count == 0
                        and web_listener_count == 0
                    ):
                        state = "STOPPED"
                    else:
                        state = "DEGRADED"
                    payload = AssistantRemoteStatus(
                        ok=True,
                        state=state,
                        process_running=distributed_count > 0,
                        process_count=distributed_count,
                        profile_review_running=profile_count > 0,
                        profile_review_count=profile_count,
                        web_running=web_running,
                        web_listener_count=web_listener_count,
                        web_version=web_version,
                        deployed_commit=(
                            str(raw.get("deployed_commit") or "").strip()
                            or None
                        ),
                        node=self.node,
                        remote_root=self.remote_root,
                        stdout_log=str(
                            raw.get("stdout_log")
                            or self.log_root + r"\assistant.out.log"
                        ),
                        stderr_log=str(
                            raw.get("stderr_log")
                            or self.log_root + r"\assistant.err.log"
                        ),
                        profile_stdout_log=str(
                            raw.get("profile_stdout_log")
                            or self.log_root + r"\profile-review.out.log"
                        ),
                        profile_stderr_log=str(
                            raw.get("profile_stderr_log")
                            or self.log_root + r"\profile-review.err.log"
                        ),
                        error=None,
                    ).as_dict()
                except Exception as exc:
                    payload = self._error_status(
                        f"remote_status_parse_failed:{type(exc).__name__}:{exc}"[:500]
                    )

        with self._lock:
            self._status_cache = (time.monotonic(), dict(payload))
        return payload

    def _error_status(self, error: str) -> dict:
        return AssistantRemoteStatus(
            ok=False,
            state="ERROR",
            process_running=False,
            process_count=0,
            profile_review_running=False,
            profile_review_count=0,
            web_running=False,
            web_listener_count=0,
            web_version=None,
            deployed_commit=None,
            node=self.node,
            remote_root=self.remote_root,
            stdout_log=self.log_root + r"\assistant.out.log",
            stderr_log=self.log_root + r"\assistant.err.log",
            profile_stdout_log=self.log_root + r"\profile-review.out.log",
            profile_stderr_log=self.log_root + r"\profile-review.err.log",
            error=error,
        ).as_dict()

    def _repair_partial_web(self) -> None:
        # Repair a recognized partial Web pair before invoking the remote helper.
        # Only Caddy/PHP are touched; distributed/profile workers stay alive.
        script = (
            "$ErrorActionPreference = 'Stop'\n"
            f"$root = '{self.remote_root}'\n"
            "$stopCmd = Join-Path $root 'scripts\\stop.cmd'\n"
            "$listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8712,8713 -ErrorAction SilentlyContinue)\n"
            "$ports = @($listeners | Select-Object -ExpandProperty LocalPort -Unique)\n"
            "$has8712 = ($ports -contains 8712)\n"
            "$has8713 = ($ports -contains 8713)\n"
            "if ($has8712 -xor $has8713) {\n"
            "    if (-not (Test-Path -LiteralPath $stopCmd -PathType Leaf)) { throw 'assistant_web_stop_missing' }\n"
            "    & $stopCmd\n"
            "    if ($LASTEXITCODE -ne 0) { throw \"assistant_web_partial_repair_stop_failed:$LASTEXITCODE\" }\n"
            "    Start-Sleep -Milliseconds 400\n"
            "    $remaining = @(Get-NetTCPConnection -State Listen -LocalPort 8712,8713 -ErrorAction SilentlyContinue)\n"
            "    if ($remaining.Count -ne 0) { throw 'assistant_web_partial_repair_incomplete' }\n"
            "    Write-Output 'EZS_ASSISTANT_WEB_PARTIAL_REPAIR_READY'\n"
            "}\n"
        )
        completed = self._run_ps(script, timeout=20)
        if completed.returncode != 0:
            error = (
                completed.stderr.strip()
                or completed.stdout.strip()
                or f"ssh_rc={completed.returncode}"
            )
            raise RuntimeError(
                f"assistant_web_partial_repair_failed:{error[:500]}"
            )

    def start(self) -> dict:
        token = self._configured_token()
        self._repair_partial_web()
        completed = self._run_remote_helper(
            "start",
            timeout=75,
            stdin_text=token + "\n",
        )
        if completed.returncode != 0:
            error = (
                completed.stderr.strip()
                or completed.stdout.strip()
                or f"ssh_rc={completed.returncode}"
            )
            raise RuntimeError(f"assistant_start_failed:{error[:500]}")
        self._status_cache = None
        deadline = time.monotonic() + 45.0
        status = self.status(force=True)
        while time.monotonic() < deadline:
            distributed_count = int(status.get("process_count") or 0)
            profile_count = int(status.get("profile_review_count") or 0)
            web_running = bool(status.get("web_running"))
            if distributed_count == 1 and profile_count == 1 and web_running:
                break
            if distributed_count > 1:
                raise RuntimeError("assistant_distributed_start_not_singleton")
            if profile_count > 1:
                raise RuntimeError("assistant_profile_start_not_singleton")
            time.sleep(0.5)
            status = self.status(force=True)
        if int(status.get("process_count") or 0) != 1:
            raise RuntimeError("assistant_distributed_start_not_singleton")
        if int(status.get("profile_review_count") or 0) != 1:
            raise RuntimeError("assistant_profile_start_not_singleton")
        if not bool(status.get("web_running")):
            raise RuntimeError("assistant_web_start_not_running")
        if int(status.get("web_listener_count") or 0) != 2:
            raise RuntimeError("assistant_web_start_not_singleton")
        return {
            "ok": True,
            "schema": "ezs.assistant-supervision.start.v1",
            "state": status.get("state"),
            "process_count": status.get("process_count"),
            "profile_review_count": status.get("profile_review_count"),
            "web_running": status.get("web_running"),
            "web_listener_count": status.get("web_listener_count"),
            "web_version": status.get("web_version"),
            "deployed_commit": status.get("deployed_commit"),
        }

    def stop(self) -> dict:
        completed = self._run_remote_helper("stop", timeout=20)
        if completed.returncode != 0:
            error = (
                completed.stderr.strip()
                or completed.stdout.strip()
                or f"ssh_rc={completed.returncode}"
            )
            raise RuntimeError(f"assistant_stop_failed:{error[:500]}")
        self._status_cache = None
        status = self.status(force=True)
        if status.get("process_running") or status.get("profile_review_running"):
            raise RuntimeError("assistant_stop_process_still_running")
        if status.get("web_running") or int(status.get("web_listener_count") or 0) != 0:
            raise RuntimeError("assistant_web_stop_still_running")
        return {
            "ok": True,
            "schema": "ezs.assistant-supervision.stop.v1",
            "state": "STOPPED",
            "process_count": 0,
            "profile_review_count": 0,
            "deployed_commit": status.get("deployed_commit"),
        }

    def tail(self, stream: str, lines: int = 250) -> dict:
        if stream not in {"stdout", "stderr"}:
            raise ValueError("assistant_log_stream_invalid")
        lines = max(20, min(int(lines), 1000))
        filename = "assistant.out.log" if stream == "stdout" else "assistant.err.log"
        path = self.log_root + "\\" + filename
        script = f"""$ErrorActionPreference = 'Stop'
$path = '{path}'
if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {{
    exit 0
}}
Get-Content -LiteralPath $path -Tail {lines}
"""
        try:
            completed = self._run_ps(script)
        except subprocess.TimeoutExpired:
            return {
                "ok": False,
                "schema": "ezs.assistant-supervision.logs.v1",
                "stream": stream,
                "path": path,
                "lines": [],
                "error": "ssh_timeout",
            }
        except OSError as exc:
            return {
                "ok": False,
                "schema": "ezs.assistant-supervision.logs.v1",
                "stream": stream,
                "path": path,
                "lines": [],
                "error": f"{type(exc).__name__}:{exc}"[:500],
            }

        if completed.returncode != 0:
            error = (
                completed.stderr.strip()
                or completed.stdout.strip()
                or f"ssh_rc={completed.returncode}"
            )
            return {
                "ok": False,
                "schema": "ezs.assistant-supervision.logs.v1",
                "stream": stream,
                "path": path,
                "lines": [],
                "error": error[:500],
            }

        return {
            "ok": True,
            "schema": "ezs.assistant-supervision.logs.v1",
            "stream": stream,
            "path": path,
            "lines": completed.stdout.splitlines(),
            "error": None,
        }
