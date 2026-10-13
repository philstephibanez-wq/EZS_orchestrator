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


@dataclass(frozen=True)
class AssistantRemoteStatus:
    ok: bool
    state: str
    process_running: bool
    process_count: int
    profile_review_running: bool
    profile_review_count: int
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
    ) -> None:
        self.node = node
        self.remote_root = remote_root
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
        return subprocess.run(
            [
                "ssh",
                self.node,
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                self._encoded(script),
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
    $commitPath = Join-Path $root 'DEPLOYED_COMMIT.txt'
    $stdoutPath = Join-Path $root 'logs\\assistant.out.log'
    $stderrPath = Join-Path $root 'logs\\assistant.err.log'
    $profileStdoutPath = Join-Path $root 'logs\\profile-review.out.log'
    $profileStderrPath = Join-Path $root 'logs\\profile-review.err.log'
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
    if (Test-Path -LiteralPath $commitPath -PathType Leaf) {{
        $commit = (Get-Content -LiteralPath $commitPath -Raw).Trim()
    }}
    [pscustomobject]@{{
        process_count = [int]$distributedMatches.Count
        profile_review_count = [int]$profileMatches.Count
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
                    if distributed_count == 1 and profile_count == 1:
                        state = "RUNNING"
                    elif distributed_count == 0 and profile_count == 0:
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
            deployed_commit=None,
            node=self.node,
            remote_root=self.remote_root,
            stdout_log=self.log_root + r"\assistant.out.log",
            stderr_log=self.log_root + r"\assistant.err.log",
            profile_stdout_log=self.log_root + r"\profile-review.out.log",
            profile_stderr_log=self.log_root + r"\profile-review.err.log",
            error=error,
        ).as_dict()

    def start(self) -> dict:
        token = self._configured_token()
        script = f"""$ErrorActionPreference = 'Stop'
    $root = '{self.remote_root}'
    $app = Join-Path $root 'app\\main.py'
    $statusWindow = Join-Path $root 'app\\status_window.pyw'
    $hostRepo = Join-Path $root 'runtime'
    $logs = Join-Path $root 'logs'
    $profileRuntime = Join-Path $env:LOCALAPPDATA 'EZStudioLab_assistant\\runtime'
    $profileStatePath = Join-Path $profileRuntime 'profile-review-watch.state.json'
    $stdoutPath = Join-Path $logs 'assistant.out.log'
    $stderrPath = Join-Path $logs 'assistant.err.log'
    $profileStdoutPath = Join-Path $logs 'profile-review.out.log'
    $profileStderrPath = Join-Path $logs 'profile-review.err.log'
    if (-not (Test-Path -LiteralPath $app -PathType Leaf)) {{ throw 'assistant_app_missing' }}
    if (-not (Test-Path -LiteralPath $statusWindow -PathType Leaf)) {{ throw 'assistant_status_window_missing' }}
    if (-not (Test-Path -LiteralPath (Join-Path $hostRepo 'python\\ezstudio\\distributed\\capabilities.py') -PathType Leaf)) {{ throw 'assistant_runtime_missing' }}
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
    if ($distributedMatches.Count -gt 1) {{ throw "assistant_duplicate_distributed_processes:$($distributedMatches.Count)" }}
    if ($profileMatches.Count -gt 1) {{ throw "assistant_duplicate_profile_processes:$($profileMatches.Count)" }}

    $token = [Console]::In.ReadLine()
    if ([string]::IsNullOrWhiteSpace($token)) {{ throw 'assistant_token_stdin_missing' }}

    $python = (Get-Command python -ErrorAction Stop).Source
    New-Item -ItemType Directory -Path $logs -Force | Out-Null
    New-Item -ItemType Directory -Path $profileRuntime -Force | Out-Null
    $env:EZSTUDIOLAB_ASSISTANT_TOKEN = $token
    $env:EZSTUDIOLAB_ASSISTANT_BASE_URL = 'http://EZSTUDIO-MAIN:8702'
    $env:EZSTUDIOLAB_ASSISTANT_NODE_ID = 'EZStudioLab_assistant-EZSTUDIO-XPS'
    $env:EZSTUDIOLAB_HOST_REPO = $hostRepo
    $env:EZSTUDIO_SHARED_MODEL_ROOT = '\\\\EZSTUDIO-MAIN\\EZModels'
    $env:EZSTUDIOLAB_ASSISTANT_MODEL_CACHE = (Join-Path $root 'models')
    $env:EZSTUDIOLAB_ASSISTANT_STATUS_FILE = (Join-Path $logs 'assistant.status.json')
    $env:PYTHONPATH = (Join-Path $hostRepo 'python')

    if ($distributedMatches.Count -eq 0) {{
        $distributed = Start-Process -FilePath $python -ArgumentList @(
            $app,'distributed-watch','--poll-seconds','5','--limit','100'
        ) -WorkingDirectory $root -WindowStyle Hidden -PassThru `
          -RedirectStandardOutput $stdoutPath `
          -RedirectStandardError $stderrPath
        Start-Sleep -Milliseconds 900
        if ($distributed.HasExited) {{
            throw "assistant_distributed_start_exited:$($distributed.ExitCode)"
        }}
    }}

    if ($profileMatches.Count -eq 0) {{
        $profile = Start-Process -FilePath $python -ArgumentList @(
            $app,
            'profile-review-auto-watch',
            '--state-file',$profileStatePath,
            '--poll-seconds','900',
            '--draft-cooldown-hours','24',
            '--abstain-cooldown-hours','168',
            '--limit','100',
            '--max-items','5',
            '--min-confidence','0.75',
            '--network-min-interval','2',
            '--network-max-response-kb','256',
            '--network-max-requests','6'
        ) -WorkingDirectory $root -WindowStyle Hidden -PassThru `
          -RedirectStandardOutput $profileStdoutPath `
          -RedirectStandardError $profileStderrPath
        Start-Sleep -Milliseconds 900
        if ($profile.HasExited) {{
            throw "assistant_profile_start_exited:$($profile.ExitCode)"
        }}
    }}

    $taskName = 'EZStudioLab Assistant Status'
    $existingStatusTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($null -ne $existingStatusTask) {{
        Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue
    }}
    $pythonw = (Get-Command pythonw.exe -ErrorAction Stop).Source
    $action = New-ScheduledTaskAction `
        -Execute $pythonw `
        -Argument ('"' + $statusWindow + '" --root "' + $root + '"')
    $principal = New-ScheduledTaskPrincipal `
        -UserId $env:USERNAME `
        -LogonType Interactive `
        -RunLevel Limited
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Principal $principal `
        -Description 'Fenêtre locale de statut EZStudioLab Assistant' `
        -Force | Out-Null
    Start-ScheduledTask -TaskName $taskName
    """
        completed = self._run_ps(script, timeout=30, stdin_text=token + "\n")
        if completed.returncode != 0:
            error = (
                completed.stderr.strip()
                or completed.stdout.strip()
                or f"ssh_rc={completed.returncode}"
            )
            raise RuntimeError(f"assistant_start_failed:{error[:500]}")
        self._status_cache = None
        status = self.status(force=True)
        if int(status.get("process_count") or 0) != 1:
            raise RuntimeError("assistant_distributed_start_not_singleton")
        if int(status.get("profile_review_count") or 0) != 1:
            raise RuntimeError("assistant_profile_start_not_singleton")
        return {
            "ok": True,
            "schema": "ezs.assistant-supervision.start.v1",
            "state": status.get("state"),
            "process_count": status.get("process_count"),
            "profile_review_count": status.get("profile_review_count"),
            "deployed_commit": status.get("deployed_commit"),
        }

    def stop(self) -> dict:
        script = f"""$ErrorActionPreference = 'Stop'
    $root = '{self.remote_root}'
    $statusPath = Join-Path $root 'logs\\assistant.status.json'
    $matches = @(
        Get-CimInstance Win32_Process | Where-Object {{
            $_.CommandLine -and
            $_.CommandLine -like '*EZStudioLab_assistant*app*main.py*' -and
            (
                $_.CommandLine -like '*distributed-watch*' -or
                $_.CommandLine -like '*profile-review-auto-watch*'
            )
        }}
    )
    foreach ($proc in $matches) {{
        Stop-Process -Id ([int]$proc.ProcessId) -Force -ErrorAction Stop
    }}
    $payload = [ordered]@{{
        schema='ezstudio.assistant-local-status.v1'
        state='STOPPED'
        activity='Assistant arrêté par Orchestrator'
        at_epoch=[DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()/1000.0
        at=[DateTime]::UtcNow.ToString('o')
    }}
    New-Item -ItemType Directory -Path (Split-Path $statusPath) -Force | Out-Null
    $tmp = $statusPath + '.tmp'
    $payload | ConvertTo-Json -Compress | Set-Content -LiteralPath $tmp -Encoding utf8
    Move-Item -LiteralPath $tmp -Destination $statusPath -Force
    """
        completed = self._run_ps(script, timeout=20)
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
