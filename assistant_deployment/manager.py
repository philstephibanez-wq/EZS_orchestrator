from __future__ import annotations

import argparse
import base64
import hashlib
import json
import shutil
import subprocess
import tempfile
import zipfile
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_LAB_ROOT = Path(r"H:\EZStudio_lab")
DEFAULT_SOURCE = Path(r"H:\EZStudioLab_assistant")
DEFAULT_NODE = "steph@192.168.1.81"
DEFAULT_REMOTE_ROOT = r"C:\EZStudioLab_assistant"
DEFAULT_REMOTE_HOST_REPO = r"C:\EZStudioLab_assistant\runtime"
ASSISTANT_DEPLOYMENT_LOG = Path(__file__).resolve().parents[1] / "logs" / "assistant-deployment.log"
SUPERVISION_HELPER = Path(__file__).resolve().parents[1] / "assistant_supervision" / "remote_helper.ps1"

RUNTIME_FILES = (
    Path("python/engine.py"),
    Path("python/ezstudio/__init__.py"),
    Path("python/ezstudio/pipeline/__init__.py"),
    Path("python/ezstudio/distributed/__init__.py"),
    Path("python/ezstudio/distributed/capabilities.py"),
    Path("python/ezstudio/distributed/model_resolver.py"),
    Path("python/ezstudio/distributed/worker_protocol.py"),
)

RUNTIME_DIRECTORIES = (
    Path("python/ezstudio/pipeline/profile"),
    Path("python/ezstudio/runtime"),
    Path("presets/profile"),
)

RUNTIME_EXCLUDED_PARTS = {"__pycache__"}
RUNTIME_EXCLUDED_SUFFIXES = {".pyc", ".pyo"}


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



def _audit_deployment(event: str, plan: DeployPlan, detail: str | None = None) -> None:
    ASSISTANT_DEPLOYMENT_LOG.parent.mkdir(parents=True, exist_ok=True)
    safe_detail = " ".join(str(detail or "").split())[:800]
    fields = [
        datetime.now(timezone.utc).isoformat(),
        f"event={event}",
        f"commit={plan.source_commit}",
        f"node={plan.node}",
        f"remote_root={plan.remote_root}",
    ]
    if safe_detail:
        fields.append(f"detail={safe_detail}")
    with ASSISTANT_DEPLOYMENT_LOG.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(" ".join(fields) + "\n")

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

    runtime_scope = [
        str(path)
        for path in (*RUNTIME_FILES, *RUNTIME_DIRECTORIES)
    ]
    if _git(["status", "--porcelain", "--", *runtime_scope], lab_root):
        raise RuntimeError("lab_runtime_dependencies_not_clean")

    source_commit = _git(["rev-parse", "HEAD"], source)

    # EZStudioLab_assistant is now an independent repository.
    # Keep the legacy field only for schema compatibility.
    parent_gitlink_commit = source_commit

    return DeployPlan(
        source=str(source),
        source_commit=source_commit,
        parent_gitlink_commit=parent_gitlink_commit,
        node=node,
        remote_root=remote_root,
        remote_host_repo=remote_host_repo,
    )


def build_status_plan(
    lab_root: Path = DEFAULT_LAB_ROOT,
    source: Path = DEFAULT_SOURCE,
    node: str = DEFAULT_NODE,
    remote_root: str = DEFAULT_REMOTE_ROOT,
    remote_host_repo: str = DEFAULT_REMOTE_HOST_REPO,
) -> DeployPlan:
    """Build a read-only deployment view without requiring a clean source tree."""
    lab_root = lab_root.resolve()
    source = source.resolve()

    if not (lab_root / ".git").exists():
        raise RuntimeError(f"lab_repo_missing:{lab_root}")
    if not source.is_dir():
        raise RuntimeError(f"assistant_source_missing:{source}")
    if not (source / ".git").exists():
        raise RuntimeError(f"assistant_git_missing:{source}")

    source_commit = _git(["rev-parse", "HEAD"], source)

    return DeployPlan(
        source=str(source),
        source_commit=source_commit,
        parent_gitlink_commit=source_commit,
        node=node,
        remote_root=remote_root,
        remote_host_repo=remote_host_repo,
    )

def _remote_script(plan: DeployPlan, remote_archive: str) -> str:
    commit = plan.source_commit
    remote_root = plan.remote_root
    runtime_root = plan.remote_host_repo
    repo_url = "https://github.com/philstephibanez-wq/EZStudioLab_assistant.git"

    return f"""$ErrorActionPreference = 'Stop'
$remoteRoot = '{remote_root}'
$staging = '{remote_root}.__new'
$previous = '{remote_root}_OLD'
$runtimeRoot = '{runtime_root}'
$runtimeStaging = Join-Path $staging 'runtime'
$legacyRuntime = 'C:\\EZStudioLab_assistant_runtime'
$legacyWebRuntime = 'C:\\var\\assistant\\web'
$legacyStateRuntime = Join-Path $env:LOCALAPPDATA 'EZStudioLab_assistant\\runtime'
$archive = Join-Path $env:USERPROFILE '{remote_archive}'
$repoUrl = '{repo_url}'
$expectedCommit = '{commit}'

function Invoke-AssistantStopIfPresent([string]$root, [string]$runtimeRoot, [string]$legacyRuntime) {{
    foreach ($candidate in @(
        (Join-Path $runtimeRoot 'assistant-supervision.ps1'),
        (Join-Path $legacyRuntime 'assistant-supervision.ps1')
    )) {{
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {{
            & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $candidate stop
            if ($LASTEXITCODE -ne 0) {{
                throw "assistant_runtime_stop_failed:$LASTEXITCODE"
            }}
            break
        }}
    }}
    $stopCmd = Join-Path $root 'scripts\\stop.cmd'
    if (Test-Path -LiteralPath $stopCmd -PathType Leaf) {{
        & $stopCmd
        if ($LASTEXITCODE -ne 0) {{
            throw "assistant_web_stop_failed:$LASTEXITCODE"
        }}
    }}
}}

if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) {{
    throw 'remote_runtime_archive_missing'
}}

Invoke-AssistantStopIfPresent $remoteRoot $runtimeRoot $legacyRuntime

$busy = @(Get-NetTCPConnection -State Listen -LocalPort 8712,8713 -ErrorAction SilentlyContinue)
if ($busy.Count -ne 0) {{
    throw 'assistant_ports_busy_before_deploy'
}}

foreach ($path in @($staging,$previous)) {{
    if (Test-Path -LiteralPath $path) {{
        Remove-Item -LiteralPath $path -Recurse -Force
    }}
}}

& git clone --branch main --single-branch $repoUrl $staging
if ($LASTEXITCODE -ne 0) {{
    throw 'assistant_git_clone_failed'
}}

$clonedCommit = (& git -C $staging rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $clonedCommit -ne $expectedCommit) {{
    throw "assistant_clone_commit_mismatch:$clonedCommit"
}}

New-Item -ItemType Directory -Force -Path $runtimeStaging | Out-Null
Expand-Archive -LiteralPath $archive -DestinationPath $runtimeStaging -Force

if (-not (Test-Path -LiteralPath (Join-Path $runtimeStaging 'assistant-supervision.ps1') -PathType Leaf)) {{
    throw 'assistant_runtime_helper_missing'
}}
if (-not (Test-Path -LiteralPath (Join-Path $runtimeStaging 'python\\ezstudio\\distributed\\capabilities.py') -PathType Leaf)) {{
    throw 'assistant_runtime_capability_missing'
}}
if (-not (Test-Path -LiteralPath (Join-Path $runtimeStaging 'runtime-manifest.json') -PathType Leaf)) {{
    throw 'assistant_runtime_manifest_missing'
}}

$oldLock = Join-Path $remoteRoot 'composer.lock'
$newLock = Join-Path $staging 'composer.lock'
$oldVendor = Join-Path $remoteRoot 'vendor'
$newVendor = Join-Path $staging 'vendor'
$reuseVendor = $false

if (
    (Test-Path -LiteralPath $oldLock -PathType Leaf) -and
    (Test-Path -LiteralPath $newLock -PathType Leaf) -and
    (Test-Path -LiteralPath (Join-Path $oldVendor 'autoload_runtime.php') -PathType Leaf)
) {{
    $oldHash = (Get-FileHash -LiteralPath $oldLock -Algorithm SHA256).Hash
    $newHash = (Get-FileHash -LiteralPath $newLock -Algorithm SHA256).Hash
    $reuseVendor = ($oldHash -eq $newHash)
}}

if ($reuseVendor) {{
    Copy-Item -LiteralPath $oldVendor -Destination $newVendor -Recurse -Force
    Write-Output 'COMPOSER_LOCK_IDENTICAL reuse_vendor'
}}
else {{
    Push-Location $staging
    try {{
        & composer install --no-interaction --prefer-dist --no-progress
        if ($LASTEXITCODE -ne 0) {{
            throw "composer_install_failed:$LASTEXITCODE"
        }}
    }}
    finally {{
        Pop-Location
    }}
}}

if (-not (Test-Path -LiteralPath (Join-Path $newVendor 'autoload_runtime.php') -PathType Leaf)) {{
    throw 'assistant_vendor_missing_after_prepare'
}}

$dirty = (& git -C $staging status --porcelain)
if ($LASTEXITCODE -ne 0) {{
    throw 'assistant_git_status_failed'
}}
if (-not [string]::IsNullOrWhiteSpace(($dirty -join ''))) {{
    throw "assistant_staging_not_clean:$($dirty -join ';')"
}}

if (Test-Path -LiteralPath $remoteRoot) {{
    Move-Item -LiteralPath $remoteRoot -Destination $previous
}}
Move-Item -LiteralPath $staging -Destination $remoteRoot
Remove-Item -LiteralPath $archive -Force

# Preserve persistent runtime state inside the single Assistant root.
$stateTarget = Join-Path $runtimeRoot 'state'
$stateSources = @(
    $legacyStateRuntime,
    (Join-Path $previous 'runtime\\state')
)
foreach ($stateSource in $stateSources) {{
    if (Test-Path -LiteralPath $stateSource -PathType Container) {{
        New-Item -ItemType Directory -Force -Path $stateTarget | Out-Null
        Copy-Item -Path (Join-Path $stateSource '*') -Destination $stateTarget -Recurse -Force -ErrorAction SilentlyContinue
    }}
}}

$deployed = (& git -C $remoteRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $deployed -ne $expectedCommit) {{
    throw "remote_commit_mismatch:$deployed"
}}
$finalDirty = (& git -C $remoteRoot status --porcelain)
if (-not [string]::IsNullOrWhiteSpace(($finalDirty -join ''))) {{
    throw "remote_worktree_not_clean:$($finalDirty -join ';')"
}}

if (-not (Test-Path -LiteralPath (Join-Path $runtimeRoot 'assistant-supervision.ps1') -PathType Leaf)) {{
    throw 'remote_supervision_helper_missing_after_install'
}}
if (-not (Test-Path -LiteralPath (Join-Path $runtimeRoot 'runtime-manifest.json') -PathType Leaf)) {{
    throw 'remote_runtime_manifest_missing_after_install'
}}
if (-not (Test-Path -LiteralPath (Join-Path $runtimeRoot 'python\\ezstudio\\pipeline\\profile\\runner.py') -PathType Leaf)) {{
    throw 'remote_profile_runner_missing_after_install'
}}
if (-not (Test-Path -LiteralPath (Join-Path $runtimeRoot 'python\\ezstudio\\pipeline\\profile\\passt_worker.py') -PathType Leaf)) {{
    throw 'remote_profile_passt_worker_missing_after_install'
}}
if (-not (Test-Path -LiteralPath (Join-Path $runtimeRoot 'python\\engine.py') -PathType Leaf)) {{
    throw 'remote_profile_shared_engine_missing_after_install'
}}
if (-not (Test-Path -LiteralPath (Join-Path $runtimeRoot 'presets\\profile\\profile-r3b35c-compat.v2b.json') -PathType Leaf)) {{
    throw 'remote_profile_preset_missing_after_install'
}}

# Rollback and legacy cleanup are deferred until the newly deployed
# Web + distributed worker + profile worker are validated live.
Write-Output 'EZS_ASSISTANT_REMOTE_DEPLOY_STAGED_OK'
Write-Output "commit=$deployed"
Write-Output "root=$remoteRoot"
Write-Output "runtime=$runtimeRoot"
Write-Output "vendor_reused=$reuseVendor"
"""

def _iter_runtime_sources() -> list[tuple[Path, Path]]:
    lab_root = DEFAULT_LAB_ROOT.resolve()
    sources: list[tuple[Path, Path]] = []

    for relative in RUNTIME_FILES:
        source_file = lab_root / relative
        if not source_file.is_file():
            raise RuntimeError(
                f"assistant_runtime_dependency_missing:{source_file}"
            )
        sources.append((relative, source_file))

    for relative_dir in RUNTIME_DIRECTORIES:
        source_dir = lab_root / relative_dir
        if not source_dir.is_dir():
            raise RuntimeError(
                f"assistant_runtime_dependency_dir_missing:{source_dir}"
            )
        for source_file in sorted(source_dir.rglob("*")):
            if not source_file.is_file():
                continue
            rel_from_dir = source_file.relative_to(source_dir)
            if any(part in RUNTIME_EXCLUDED_PARTS for part in rel_from_dir.parts):
                continue
            if source_file.suffix.lower() in RUNTIME_EXCLUDED_SUFFIXES:
                continue
            sources.append((relative_dir / rel_from_dir, source_file))

    if not SUPERVISION_HELPER.is_file():
        raise RuntimeError("assistant_supervision_helper_missing")
    sources.append((Path("assistant-supervision.ps1"), SUPERVISION_HELPER))
    return sorted(sources, key=lambda item: item[0].as_posix())


def _runtime_fingerprint() -> str:
    digest = hashlib.sha256()
    for relative, source_file in _iter_runtime_sources():
        digest.update(relative.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update(source_file.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()



def _build_bundle(plan: DeployPlan, destination: Path) -> None:
    """Build the scientific/runtime payload installed under remote_root\\runtime."""
    bundle_root = destination.parent / "runtime-bundle"
    bundle_root.mkdir(parents=True, exist_ok=True)

    for relative, source_file in _iter_runtime_sources():
        target_file = bundle_root / relative
        target_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_file, target_file)

    manifest = {
        "schema": "ezs.assistant-runtime-manifest.v1",
        "fingerprint": _runtime_fingerprint(),
        "assistant_commit": plan.source_commit,
    }
    (bundle_root / "runtime-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    shutil.make_archive(
        str(destination.with_suffix("")),
        "zip",
        root_dir=bundle_root,
    )
    if not destination.is_file():
        raise RuntimeError("assistant_runtime_bundle_archive_failed")


def _remote_deployed_commit(
    plan: DeployPlan,
) -> tuple[bool, str | None, str | None]:
    script = (
        "$ErrorActionPreference = 'Stop'\n"
        f"$root = '{plan.remote_root}'\n"
        "$gitDir = Join-Path $root '.git'\n"
        "if (-not (Test-Path -LiteralPath $gitDir -PathType Container)) { exit 3 }\n"
        "$commit = (& git -C $root rev-parse HEAD).Trim()\n"
        "if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($commit)) { exit 4 }\n"
        "Write-Output $commit\n"
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
                row.lower()
                for row in reversed(rows)
                if len(row) == 40
                and all(ch in "0123456789abcdefABCDEF" for ch in row)
            ),
            None,
        )
        if commit is None:
            return False, None, "remote_commit_output_invalid"
        return True, commit, None

    if completed.returncode == 3:
        return True, None, None

    error = (
        completed.stderr.strip()
        or completed.stdout.strip()
        or f"ssh_rc={completed.returncode}"
    )
    return False, None, error[:500]


def _version_from_file(path: Path) -> str | None:
    try:
        value = path.read_text(encoding="utf-8-sig").strip()
    except OSError:
        return None
    return value or None


def _source_version(plan: DeployPlan) -> str | None:
    return _version_from_file(Path(plan.source) / "VERSION")


def _remote_runtime_state(plan: DeployPlan) -> tuple[bool, str | None, bool, str | None]:
    script = (
        "$ErrorActionPreference = 'Stop'\n"
        f"$runtime = '{plan.remote_host_repo}'\n"
        "$manifest = Join-Path $runtime 'runtime-manifest.json'\n"
        "$legacy = 'C:\\\\EZStudioLab_assistant_runtime'\n"
        "$fingerprint = $null\n"
        "if (Test-Path -LiteralPath $manifest -PathType Leaf) {\n"
        "  $data = Get-Content -LiteralPath $manifest -Raw | ConvertFrom-Json\n"
        "  $fingerprint = [string]$data.fingerprint\n"
        "}\n"
        "[pscustomobject]@{\n"
        "  fingerprint = $fingerprint\n"
        "  legacy_present = [bool](Test-Path -LiteralPath $legacy)\n"
        "} | ConvertTo-Json -Compress\n"
    )
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    try:
        completed = subprocess.run(
            [
                "ssh", plan.node, "powershell", "-NoProfile", "-NonInteractive",
                "-ExecutionPolicy", "Bypass", "-EncodedCommand", encoded,
            ],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return False, None, False, "ssh_timeout"
    except OSError as exc:
        return False, None, False, f"{type(exc).__name__}:{exc}"[:500]

    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip() or f"ssh_rc={completed.returncode}"
        return False, None, False, error[:500]
    try:
        rows = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        raw = json.loads(rows[-1])
        fingerprint = str(raw.get("fingerprint") or "").strip() or None
        legacy_present = bool(raw.get("legacy_present"))
        return True, fingerprint, legacy_present, None
    except Exception as exc:
        return False, None, False, f"remote_runtime_status_parse_failed:{type(exc).__name__}:{exc}"[:500]

def _remote_deployed_version(
    plan: DeployPlan,
) -> tuple[bool, str | None, str | None]:
    script = (
        "$ErrorActionPreference = 'Stop'\n"
        f"$path = '{plan.remote_root}\\VERSION'\n"
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
        rows = [
            line.strip()
            for line in completed.stdout.splitlines()
            if line.strip()
        ]
        value = rows[-1] if rows else ""
        if not value:
            return False, None, "remote_version_output_invalid"
        return True, value, None

    if completed.returncode == 3:
        return True, None, None

    error = (
        completed.stderr.strip()
        or completed.stdout.strip()
        or f"ssh_rc={completed.returncode}"
    )
    return False, None, error[:500]


def deployment_status(plan: DeployPlan) -> dict:
    source_version = _source_version(plan)
    source_dirty = bool(_git(["status", "--porcelain"], Path(plan.source)))
    reachable, deployed_commit, error = _remote_deployed_commit(plan)

    deployed_version = None
    version_error = None
    runtime_reachable = False
    deployed_runtime_fingerprint = None
    legacy_runtime_present = False
    runtime_error = None
    expected_runtime_fingerprint = _runtime_fingerprint()

    if reachable:
        version_reachable, deployed_version, version_error = (
            _remote_deployed_version(plan)
        )
        if not version_reachable and version_error is None:
            version_error = "remote_version_unreachable"
        (
            runtime_reachable,
            deployed_runtime_fingerprint,
            legacy_runtime_present,
            runtime_error,
        ) = _remote_runtime_state(plan)

    runtime_current = (
        runtime_reachable
        and deployed_runtime_fingerprint == expected_runtime_fingerprint
        and not legacy_runtime_present
    )

    if not reachable:
        state = "UNREACHABLE"
    elif deployed_commit is None:
        state = "NOT_DEPLOYED"
    elif source_dirty:
        state = "LOCAL_CHANGES"
    elif deployed_commit == plan.source_commit and runtime_current:
        state = "UP_TO_DATE"
    else:
        state = "UPDATE_AVAILABLE"

    return {
        "ok": reachable,
        "schema": "ezs.assistant-deployment.status.v1",
        "state": state,
        "source_version": source_version,
        "deployed_version": deployed_version,
        "source_dirty": source_dirty,
        "source_commit": plan.source_commit,
        "deployed_commit": deployed_commit,
        "runtime_current": runtime_current,
        "runtime_fingerprint": expected_runtime_fingerprint,
        "deployed_runtime_fingerprint": deployed_runtime_fingerprint,
        "legacy_runtime_present": legacy_runtime_present,
        "node": plan.node,
        "remote_root": plan.remote_root,
        "remote_runtime": plan.remote_host_repo,
        "error": error,
        "version_error": version_error,
        "runtime_error": runtime_error,
    }

def deploy(plan: DeployPlan) -> dict:
    _audit_deployment("START", plan)
    try:
        if shutil.which("ssh") is None:
            raise RuntimeError("ssh_not_found")
        if shutil.which("scp") is None:
            raise RuntimeError("scp_not_found")

        short = plan.source_commit[:12]
        remote_archive_name = f"EZStudioLab_assistant-runtime-{short}.zip"

        with tempfile.TemporaryDirectory(prefix="ezs-assistant-deploy-") as tmp:
            archive = Path(tmp) / remote_archive_name
            _build_bundle(plan, archive)

            remote_script_name = (
                f"EZStudioLab_assistant-install-{short}.ps1"
            )
            remote_script_path = Path(tmp) / remote_script_name
            remote_script_path.write_text(
                _remote_script(plan, remote_archive_name),
                encoding="utf-8-sig",
                newline="\r\n",
            )

            try:
                copied = subprocess.run(
                    [
                        "scp",
                        str(archive),
                        str(remote_script_path),
                        f"{plan.node}:.",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=120,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError("assistant_scp_timeout") from exc
            if copied.returncode != 0:
                raise RuntimeError(
                    f"assistant_scp_failed:{copied.stderr.strip()}"
                )

            try:
                installed = subprocess.run(
                    [
                        "ssh",
                        plan.node,
                        "powershell",
                        "-NoProfile",
                        "-ExecutionPolicy",
                        "Bypass",
                        "-File",
                        f".\\{remote_script_name}",
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=120,
                )
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError(
                    "assistant_remote_install_timeout"
                ) from exc
            finally:
                cleanup_command = (
                    "$ErrorActionPreference='SilentlyContinue';"
                    f"Remove-Item -LiteralPath '.\\{remote_script_name}' "
                    "-Force -ErrorAction SilentlyContinue;"
                    f"Remove-Item -LiteralPath '.\\{remote_archive_name}' "
                    "-Force -ErrorAction SilentlyContinue"
                )
                subprocess.run(
                    [
                        "ssh",
                        plan.node,
                        "powershell",
                        "-NoProfile",
                        "-NonInteractive",
                        "-Command",
                        cleanup_command,
                    ],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    timeout=30,
                )

            if installed.returncode != 0:
                raise RuntimeError(
                    "assistant_remote_install_failed:"
                    + (
                        installed.stderr.strip()
                        or installed.stdout.strip()
                    )
                )

        result = {
            "ok": True,
            "schema": "ezs.assistant-deployment.v1",
            "commit": plan.source_commit,
            "node": plan.node,
            "remote_root": plan.remote_root,
            "remote_host_repo": plan.remote_host_repo,
            "stdout": installed.stdout.strip(),
            "secrets_deployed": False,
            "scientific_execution_started": False,
            "application_deploy_mode": "git_clean_clone",
        }
    except Exception as exc:
        _audit_deployment("FAIL", plan, f"{type(exc).__name__}:{exc}")
        raise

    _audit_deployment("OK", plan, f"remote_host_repo={plan.remote_host_repo}")
    return result


def _run_remote_lifecycle_script(
    plan: DeployPlan,
    script: str,
    *,
    timeout: int = 60,
) -> subprocess.CompletedProcess[str]:
    encoded = base64.b64encode(script.encode("utf-16le")).decode("ascii")
    return subprocess.run(
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
        timeout=timeout,
    )


def finalize_deployment(plan: DeployPlan) -> dict:
    """Delete rollback/legacy trees only after the new runtime is live."""
    script = f"""$ErrorActionPreference = 'Stop'
$root = '{plan.remote_root}'
$previous = '{plan.remote_root}_OLD'
$runtime = '{plan.remote_host_repo}'
$legacyRuntime = 'C:\\EZStudioLab_assistant_runtime'
$legacyWebRuntime = 'C:\\var\\assistant\\web'
$legacyStateRuntime = Join-Path $env:LOCALAPPDATA 'EZStudioLab_assistant\\runtime'

$listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8712,8713 -ErrorAction SilentlyContinue)
$ports = @($listeners | Select-Object -ExpandProperty LocalPort -Unique)
if (-not ($ports -contains 8712) -or -not ($ports -contains 8713)) {{
    throw 'assistant_finalize_web_not_running'
}}

$distributed = @(
    Get-CimInstance Win32_Process | Where-Object {{
        $_.CommandLine -and
        $_.CommandLine -like '*EZStudioLab_assistant*app*main.py*' -and
        $_.CommandLine -like '*distributed-watch*'
    }}
)
$profile = @(
    Get-CimInstance Win32_Process | Where-Object {{
        $_.CommandLine -and
        $_.CommandLine -like '*EZStudioLab_assistant*app*main.py*' -and
        $_.CommandLine -like '*profile-review-auto-watch*'
    }}
)
if ($distributed.Count -ne 1) {{
    throw "assistant_finalize_distributed_not_singleton:$($distributed.Count)"
}}
if ($profile.Count -ne 1) {{
    throw "assistant_finalize_profile_not_singleton:$($profile.Count)"
}}
if (-not (Test-Path -LiteralPath (Join-Path $runtime 'state') -PathType Container)) {{
    throw 'assistant_finalize_state_missing'
}}
if (-not (Test-Path -LiteralPath (Join-Path $runtime 'web') -PathType Container)) {{
    throw 'assistant_finalize_web_runtime_missing'
}}

foreach ($legacy in @($legacyRuntime,$legacyWebRuntime,$legacyStateRuntime,$previous)) {{
    if (Test-Path -LiteralPath $legacy) {{
        Remove-Item -LiteralPath $legacy -Recurse -Force
    }}
}}
foreach ($legacy in @($legacyRuntime,$legacyWebRuntime,$legacyStateRuntime,$previous)) {{
    if (Test-Path -LiteralPath $legacy) {{
        throw "assistant_finalize_legacy_still_present:$legacy"
    }}
}}
Write-Output 'EZS_ASSISTANT_REMOTE_DEPLOY_FINALIZE_OK'
"""
    completed = _run_remote_lifecycle_script(plan, script)
    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip() or f"ssh_rc={completed.returncode}"
        raise RuntimeError(f"assistant_finalize_failed:{error[:500]}")
    return {
        "ok": True,
        "schema": "ezs.assistant-deployment.finalize.v1",
        "stdout": completed.stdout.strip(),
    }


def rollback_deployment(plan: DeployPlan) -> dict:
    """Restore the previous Assistant root when live validation fails."""
    script = f"""$ErrorActionPreference = 'Stop'
$root = '{plan.remote_root}'
$previous = '{plan.remote_root}_OLD'
$runtime = '{plan.remote_host_repo}'
$helper = Join-Path $runtime 'assistant-supervision.ps1'
if (Test-Path -LiteralPath $helper -PathType Leaf) {{
    & powershell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $helper stop
}}
if (-not (Test-Path -LiteralPath $previous -PathType Container)) {{
    throw 'assistant_rollback_previous_missing'
}}
if (Test-Path -LiteralPath $root) {{
    Remove-Item -LiteralPath $root -Recurse -Force
}}
Move-Item -LiteralPath $previous -Destination $root
Write-Output 'EZS_ASSISTANT_REMOTE_DEPLOY_ROLLBACK_OK'
"""
    completed = _run_remote_lifecycle_script(plan, script)
    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip() or f"ssh_rc={completed.returncode}"
        raise RuntimeError(f"assistant_rollback_failed:{error[:500]}")
    return {
        "ok": True,
        "schema": "ezs.assistant-deployment.rollback.v1",
        "stdout": completed.stdout.strip(),
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
