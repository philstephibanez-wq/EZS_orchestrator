"""Supervision locale de l'Assistant Docker MAIN, sans SSH XPS."""
import json
import subprocess
import shutil
import urllib.request
from pathlib import Path

ROOT = Path("H:/EZStudioLab_assistant")
COMPOSE = ROOT / "docker/main/compose.yaml"

def docker(args):
    exe = shutil.which("docker")
    if exe is None:
        candidate = Path("H:/Docker/Desktop/resources/bin/docker.exe")
        exe = str(candidate) if candidate.is_file() else None
    if exe is None:
        raise RuntimeError("docker_executable_not_found_on_MAIN")
    p = subprocess.run([exe] + args, capture_output=True, text=True, timeout=30)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[:400])
    return p.stdout

def ready(port, path="/"):
    try:
        with urllib.request.urlopen("http://127.0.0.1:%s%s" % (port, path), timeout=2) as response:
            return response.status == 200
    except (OSError, ValueError):
        return False

class MainSupervisor:
    def status(self, force=False):
        version_path = ROOT / "VERSION"
        version = version_path.read_text(encoding="utf-8-sig").strip() if version_path.exists() else None
        try:
            containers = [json.loads(line) for line in docker(["ps", "--format", "{{json .}}"]).splitlines() if line.strip()]
            names = [str(c.get("Names", "")) for c in containers]
            web = any("ezstudio-assistant-main-smoke-assistant-web-smoke" in n for n in names)
            cuda = any("ezstudio-assistant-main-cuda-llama-cuda-smoke" in n for n in names)
            web_ok = web and ready(18713)
            cuda_ok = cuda and ready(18720, "/health")
            state = "ONLINE" if web_ok and cuda_ok else ("DEGRADED" if web or cuda else "STOPPED")
            return dict(ok=True, schema="ezs.assistant-supervision.status.v2", deployment_mode="main-docker",
                        state=state, web_running=web_ok, inference_running=cuda_ok,
                        web_listener_count=int(web_ok), process_running=bool(web or cuda),
                        process_count=int(web)+int(cuda), profile_review_running=False,
                        profile_review_count=0, web_version=version, deployed_commit=None,
                        node="MAIN", remote_root=str(ROOT), stdout_log=None, stderr_log=None,
                        profile_stdout_log=None, profile_stderr_log=None, error=None,
                        inventory_online=0, inventory_count=0)
        except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
            return dict(ok=False, deployment_mode="main-docker", state="ERROR", error=str(exc)[:400])

    def start(self):
        if not COMPOSE.is_file():
            raise RuntimeError("main_web_compose_missing")
        docker(["compose", "-f", str(COMPOSE), "--profile", "smoke", "up", "-d",
                "--no-build", "--no-recreate", "assistant-web-smoke"])
        return self.status(True)

    def stop(self):
        if not COMPOSE.is_file():
            raise RuntimeError("main_web_compose_missing")
        docker(["compose", "-f", str(COMPOSE), "--profile", "smoke", "stop", "assistant-web-smoke"])
        return self.status(True)

    def tail(self, stream):
        return {"ok": False, "error": "Legacy XPS logs unavailable in MAIN Docker mode"}
