from __future__ import annotations

import argparse
import base64
import json
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path


DEFAULT_LAB_ROOT = Path(r"H:\EZStudio_lab")
DEFAULT_SOURCE = DEFAULT_LAB_ROOT / "EZStudioLab_assistant"
DEFAULT_NODE = "steph@192.168.1.81"
DEFAULT_REMOTE_ROOT = r"C:\EZStudioLab_assistant"
DEFAULT_REMOTE_HOST_REPO = r"C:\EZStudioLab_assistant\runtime"

RUNTIME_FILES = (
    Path("python/ezstudio/__init__.py"),
    Path("python/ezstudio/distributed/__init__.py"),
    Path("python/ezstudio/distributed/capabilities.py"),
    Path("python/ezstudio/distributed/model_resolver.py"),
    Path("python/ezstudio/distributed/worker_protocol.py"),
)


@dataclass(frozen=True)
class DeployPlan:
    source: str
    source_commit: str
    parent_gitlink_commit: str
    node: str
    remote_root: str
    remote_host_repo: str

    def as_dict(self) -> dict:
        return asdict(self)


def _run(
    args: list[str],
    *,
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=str(cwd) if cwd else None,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=check,
    )


def _git(args: list[str], cwd: Path) -> str:
    return _run(["git", *args], cwd=cwd).stdout.strip()


def build_plan(
    lab_root: Path = DEFAULT_LAB_ROOT,
    source: Path = DEFAULT_SOURCE,
    node: str = DEFAULT_NODE,
    remote_root: str = DEFAULT_REMOTE_ROOT,
    remote_host_repo: str = DEFAULT_REMOTE_HOST_REPO,
) -> DeployPlan:
    lab_root = lab_root.resolve()
    source = source.resolve()

    if not (lab_root / ".git").exists():
        raise RuntimeError(f"lab_repo_missing:{lab_root}")
    if not source.is_dir():
        raise RuntimeError(f"assistant_source_missing:{source}")
    if not (source / ".git").exists():
        raise RuntimeError(f"assistant_git_missing:{source}")

    if _git(["status", "--porcelain"], source):
        raise RuntimeError("assistant_working_tree_not_clean")

    source_commit = _git(["rev-parse", "HEAD"], source)
    tree_line = _git(["ls-tree", "HEAD", "EZStudioLab_assistant"], lab_root)
    parts = tree_line.split()
    if len(parts) < 3 or parts[1] != "commit":
        raise RuntimeError("assistant_parent_gitlink_missing")
    parent_gitlink_commit = parts[2]

    if source_commit != parent_gitlink_commit:
        raise RuntimeError(
            f"assistant_source_not_parent_pinned:"
            f"source={source_commit}:gitlink={parent_gitlink_commit}"
        )

    return DeployPlan(
        source=str(source),
        source_commit=source_commit,
        parent_gitlink_commit=parent_gitlink_commit,
        node=node,
        remote_root=remote_root,
        remote_host_repo=remote_host_repo,
    )


def _remote_script(plan: DeployPlan, remote_archive: str) -> str:
    commit = plan.source_commit
    remote_root = plan.remote_root
    host_repo = plan.remote_host_repo

    return f"""$ErrorActionPreference = 'Stop'
$remoteRoot = '{remote_root}'
$staging = '{remote_root}.__new'
$previous = '{remote_root}.__previous'
$archive = Join-Path $env:USERPROFILE '{remote_archive}'
$hostRepo = '{host_repo}'

if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) {{
    throw 'remote_archive_missing'
}}

if (Test-Path -LiteralPath $staging) {{
    Remove-Item -LiteralPath $staging -Recurse -Force
}}
New-Item -ItemType Directory -Force -Path $staging | Out-Null
Expand-Archive -LiteralPath $archive -DestinationPath $staging -Force

if (-not (Test-Path -LiteralPath (Join-Path $staging 'app\\main.py') -PathType Leaf)) {{
    throw 'remote_staging_app_missing'
}}
if (-not (Test-Path -LiteralPath (Join-Path $staging 'scripts\\start-EZStudioLab_assistant.ps1') -PathType Leaf)) {{
    throw 'remote_staging_launcher_missing'
}}
if (-not (Test-Path -LiteralPath (Join-Path $staging 'runtime\\python\\ezstudio\\distributed\\capabilities.py') -PathType Leaf)) {{
    throw 'remote_staging_runtime_missing'
}}

Set-Content -LiteralPath (Join-Path $staging 'DEPLOYED_COMMIT.txt') -Value '{commit}' -Encoding ascii
Set-Content -LiteralPath (Join-Path $staging 'HOST_REPO.txt') -Value $hostRepo -Encoding ascii

if (Test-Path -LiteralPath $previous) {{
    Remove-Item -LiteralPath $previous -Recurse -Force
}}
if (Test-Path -LiteralPath $remoteRoot) {{
    Move-Item -LiteralPath $remoteRoot -Destination $previous
}}
Move-Item -LiteralPath $staging -Destination $remoteRoot
Remove-Item -LiteralPath $archive -Force

$deployed = (Get-Content -LiteralPath (Join-Path $remoteRoot 'DEPLOYED_COMMIT.txt') -Raw).Trim()
if ($deployed -ne '{commit}') {{
    throw "remote_commit_mismatch:$deployed"
}}
if (-not (Test-Path -LiteralPath (Join-Path $hostRepo 'python\\ezstudio\\distributed\\capabilities.py') -PathType Leaf)) {{
    throw 'remote_runtime_missing_after_install'
}}

Write-Output 'EZS_ASSISTANT_REMOTE_DEPLOY_OK'
Write-Output "commit=$deployed"
Write-Output "root=$remoteRoot"
Write-Output "host_repo=$hostRepo"
"""


def _build_bundle(plan: DeployPlan, destination: Path) -> None:
    source = Path(plan.source)
    lab_root = DEFAULT_LAB_ROOT.resolve()

    assistant_archive = destination.parent / "assistant-source.zip"
    completed = subprocess.run(
        ["git", "archive", "--format=zip", f"--output={assistant_archive}", "HEAD"],
        cwd=str(source),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0 or not assistant_archive.is_file():
        raise RuntimeError(
            f"assistant_archive_failed:{completed.stderr.strip()}"
        )

    bundle_root = destination.parent / "bundle"
    bundle_root.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(assistant_archive, "r") as src_zip:
        src_zip.extractall(bundle_root)

    for relative in RUNTIME_FILES:
        source_file = lab_root / relative
        if not source_file.is_file():
            raise RuntimeError(
                f"assistant_runtime_dependency_missing:{source_file}"
            )
        target_file = bundle_root / "runtime" / relative
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)

    shutil.make_archive(
        str(destination.with_suffix("")),
        "zip",
        root_dir=bundle_root,
    )
    if not destination.is_file():
        raise RuntimeError("assistant_bundle_archive_failed")



def _remote_deployed_commit(plan: DeployPlan) -> tuple[bool, str | None, str | None]:
    script = (
        "$ErrorActionPreference = 'Stop'\n"
        f"$path = '{plan.remote_root}\\DEPLOYED_COMMIT.txt'\n"
        "if (Test-Path -LiteralPath $path -PathType Leaf) {\n"
        "    Write-Output ((Get-Content -LiteralPath $path -Raw).Trim())\n"
        "    exit 0\n"
        "}\n"
        "exit 3\n"
    )
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    try:
        completed = subprocess.run(
            [
                "ssh",
                plan.node,
                "powershell",
                "-NoProfile",
                "-NonInteractive",
                "-ExecutionPolicy",
                "Bypass",
                "-EncodedCommand",
                encoded,
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return False, None, "ssh_timeout"
    except OSError as exc:
        return False, None, f"{type(exc).__name__}:{exc}"[:500]

    if completed.returncode == 0:
        rows = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        commit = next(
            (
                row
                for row in reversed(rows)
                if len(row) == 40
                and all(ch in "0123456789abcdefABCDEF" for ch in row)
            ),
            None,
        )
        if commit is None:
            return False, None, "remote_commit_output_invalid"
        return True, commit.lower(), None

    if completed.returncode == 3:
        return True, None, None

    error = (
        completed.stderr.strip()
        or completed.stdout.strip()
        or f"ssh_rc={completed.returncode}"
    )
    return False, None, error[:500]

def deployment_status(plan: DeployPlan) -> dict:
    reachable, deployed_commit, error = _remote_deployed_commit(plan)
    if not reachable:
        state = "UNREACHABLE"
    elif deployed_commit is None:
        state = "NOT_DEPLOYED"
    elif deployed_commit == plan.source_commit:
        state = "UP_TO_DATE"
    else:
        state = "UPDATE_AVAILABLE"
    return {
        "ok": reachable,
        "schema": "ezs.assistant-deployment.status.v1",
        "state": state,
        "source_commit": plan.source_commit,
        "deployed_commit": deployed_commit,
        "node": plan.node,
        "remote_root": plan.remote_root,
        "error": error,
    }

def deploy(plan: DeployPlan) -> dict:
    if shutil.which("ssh") is None:
        raise RuntimeError("ssh_not_found")
    if shutil.which("scp") is None:
        raise RuntimeError("scp_not_found")

    short = plan.source_commit[:12]
    remote_archive_name = f"EZStudioLab_assistant-{short}.zip"

    with tempfile.TemporaryDirectory(prefix="ezs-assistant-deploy-") as tmp:
        archive = Path(tmp) / remote_archive_name
        _build_bundle(plan, archive)

        copied = subprocess.run(
            ["scp", str(archive), f"{plan.node}:{remote_archive_name}"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if copied.returncode != 0:
            raise RuntimeError(
                f"assistant_scp_failed:{copied.stderr.strip()}"
            )

    remote = _remote_script(plan, remote_archive_name)
    encoded = base64.b64encode(remote.encode("utf-16le")).decode("ascii")
    installed = subprocess.run(
        [
            "ssh",
            plan.node,
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-EncodedCommand",
            encoded,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if installed.returncode != 0:
        raise RuntimeError(
            "assistant_remote_install_failed:"
            + (installed.stderr.strip() or installed.stdout.strip())
        )

    return {
        "ok": True,
        "schema": "ezs.assistant-deployment.v1",
        "commit": plan.source_commit,
        "node": plan.node,
        "remote_root": plan.remote_root,
        "remote_host_repo": plan.remote_host_repo,
        "stdout": installed.stdout.strip(),
        "secrets_deployed": False,
        "scientific_execution_started": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(prog="EZS assistant deployment")
    parser.add_argument("command", choices=["plan", "deploy"])
    parser.add_argument("--lab-root", default=str(DEFAULT_LAB_ROOT))
    parser.add_argument("--source", default=str(DEFAULT_SOURCE))
    parser.add_argument("--node", default=DEFAULT_NODE)
    parser.add_argument("--remote-root", default=DEFAULT_REMOTE_ROOT)
    parser.add_argument(
        "--remote-host-repo",
        default=DEFAULT_REMOTE_HOST_REPO,
    )
    args = parser.parse_args()

    plan = build_plan(
        lab_root=Path(args.lab_root),
        source=Path(args.source),
        node=args.node,
        remote_root=args.remote_root,
        remote_host_repo=args.remote_host_repo,
    )

    if args.command == "plan":
        print(
            json.dumps(
                {
                    "ok": True,
                    "schema": "ezs.assistant-deployment.plan.v1",
                    **plan.as_dict(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    print(json.dumps(deploy(plan), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
