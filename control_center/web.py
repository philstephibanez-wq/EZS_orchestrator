from __future__ import annotations

import argparse
import json
import secrets
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import asdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from caddy_manager.manager import CaddyManager
from config.loader import load_runtime_config
from contracts.target import Target
from control_center.log_tools import LogTools
from control_center.job_history import JobHistory
from gateway_manager.manager import GatewayManager
from prod_lifecycle.manager import ProdLifecycleManager
from runtime_guard.activity import analysis_execution_active
from server_manager.manager import ServerManager
from server_manager.process import clear_process_cache, pid_alive
from transport.jobs import JobTransport
from transport.targets import TargetRegistry

HOST = "127.0.0.1"
DEFAULT_PORT = 8700
SNAPSHOT_CACHE_SECONDS = 1.0


def _read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _tail(path: Path, max_lines: int = 80) -> list[str]:
    if not path.is_file():
        return []
    try:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()[-max_lines:]
    except Exception as exc:
        return [f"[log read error] {exc}"]


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
        self.job_history = JobHistory(self.config.orchestrator_root)
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
                "running": False, "pid": None, "target": None,
                "poll_seconds": None, "state": "stopped",
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
                "running": False, "pid": None, "target": None,
                "poll_seconds": None, "state": "stopped",
                "heartbeat": heartbeat.get("at"),
            }

        return {
            "running": True,
            "pid": pid,
            "target": meta.get("target"),
            "poll_seconds": meta.get("poll_seconds"),
            "state": heartbeat.get("state", "unknown"),
            "heartbeat": heartbeat.get("at"),
        }

    def _queue(self, target: Target) -> dict:
        try:
            jobs = self.transport.queue(target)
            return {"ok": True, "count": len(jobs), "jobs": jobs[:8]}
        except Exception as exc:
            return {"ok": False, "count": None, "jobs": [], "error": str(exc)}

    def _snapshot_uncached(self) -> dict:
        clear_process_cache()
        started = time.monotonic()
        dev = self.servers.view(Target.DEV)
        prod = self.prod.view()
        dev_caddy = self.caddy.view(Target.DEV)
        elapsed_ms = round((time.monotonic() - started) * 1000.0, 1)
        return {
            "at": datetime.now(timezone.utc).isoformat(),
            "snapshot_ms": elapsed_ms,
            "analysis_active": bool(analysis_execution_active(self.runtime)),
            "service": self._service_status(),
            "dev": {
                "server": asdict(dev),
                "caddy": asdict(dev_caddy),
                "queue": self._queue(Target.DEV),
                "analysis_python": str(self.config.analysis_python_for(Target.DEV)),
                "transport": self.config.transport_url_for(Target.DEV),
            },
            "prod": {
                "lifecycle": prod.as_dict(),
                "queue": self._queue(Target.PROD),
                "analysis_python": str(self.config.analysis_python_for(Target.PROD)),
                "transport": self.config.transport_url_for(Target.PROD),
            },
        }

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
                return {"ok": True, "message": f"DEV backend active pid={view.pid}"}
            if name == "dev-server-stop":
                view = self.servers.stop(Target.DEV)
                self._invalidate_snapshot()
                return {"ok": True, "message": "DEV backend stopped" if not view.process_alive else "DEV backend still active"}
            if name == "dev-server-restart":
                view = self.servers.restart(Target.DEV)
                self._invalidate_snapshot()
                return {"ok": True, "message": f"DEV backend restarted pid={view.pid}"}
            if name == "dev-caddy-start":
                view = self.caddy.start(Target.DEV)
                self._invalidate_snapshot()
                return {"ok": True, "message": f"DEV Caddy active pid={view.pid}"}

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
                    capture_output=True, text=True, timeout=10,
                )
                self._invalidate_snapshot()
                output = (completed.stdout or completed.stderr).strip()
                return {"ok": completed.returncode in (0, 3), "message": output or f"returncode={completed.returncode}"}

            if name == "service-stop":
                completed = subprocess.run(
                    [sys.executable, "-m", "service.service_cli", "stop", "--wait-seconds", "15"],
                    cwd=str(self.config.orchestrator_root),
                    capture_output=True, text=True, timeout=20,
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
                return {"ok": True, "message": f"{result.cleared} log file(s) cleared logically; physical files, servers and worker untouched"}

            raise ValueError(f"unsupported_action:{name}")

    def jobs(self) -> dict:
        return self.job_history.payload(limit=40)

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
        }


HTML = '''<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>EZS Orchestrator - Control Center R3.15</title>
<style>
:root{color-scheme:dark;--bg:#0b1114;--panel:#111a1f;--panel2:#162229;--line:#26363f;--text:#ecf5f4;--muted:#93a8ad;--accent:#49d1bd;--ok:#5ed38b;--warn:#f2c96d;--bad:#ff7b7b;--prod:#98a5ff}
*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,Segoe UI,Arial;background:var(--bg);color:var(--text)}
header{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 24px;border-bottom:1px solid var(--line);background:#0d1519}
.brand{font-weight:800;letter-spacing:.04em;font-size:18px}.brand b{color:var(--accent)}.sub{color:var(--muted);font-size:12px}
main{padding:20px;max-width:1500px;margin:auto}.topgrid{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:14px;margin-bottom:14px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;min-width:0}.card h2{margin:0 0 12px;font-size:14px}
.statusrow{display:flex;align-items:center;gap:9px;flex-wrap:wrap}.dot{width:10px;height:10px;border-radius:50%;background:var(--muted);display:inline-block}.dot.ok{background:var(--ok)}.dot.warn{background:var(--warn)}.dot.bad{background:var(--bad)}
.big{font-size:22px;font-weight:750;margin:6px 0}.muted{color:var(--muted)}.targets{display:grid;grid-template-columns:1fr 1fr;gap:14px}.target.dev{border-top:3px solid var(--accent)}.target.prod{border-top:3px solid var(--prod)}
.kv{display:grid;grid-template-columns:150px minmax(0,1fr);gap:7px 10px;margin:10px 0}.kv dt{color:var(--muted)}.kv dd{margin:0;overflow-wrap:anywhere}
.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}button,a.btn{appearance:none;border:1px solid var(--line);background:var(--panel2);color:var(--text);border-radius:9px;padding:9px 12px;text-decoration:none;cursor:pointer;font-weight:650}
button.primary,a.primary{background:#173b37;border-color:#27655d}button.danger{background:#371d21;border-color:#6f343c}button.warn{background:#3a3019;border-color:#6e5928}button:disabled{opacity:.45;cursor:not-allowed}
.queue{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}.queue strong{font-size:19px}.banner{margin-bottom:14px;padding:11px 14px;border:1px solid var(--line);border-radius:10px;background:var(--panel)}.banner.active{border-color:#775a27;background:#251f13}
.jobs-panel{margin-top:14px}.jobs-head{display:flex;align-items:center;justify-content:space-between;gap:12px;margin-bottom:10px}.jobs-table-wrap{overflow:auto;border:1px solid var(--line);border-radius:10px}.jobs-table{width:100%;border-collapse:collapse;min-width:820px}.jobs-table th,.jobs-table td{padding:9px 10px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}.jobs-table th{color:var(--muted);font-size:12px;background:#0d1519}.jobs-table tr:last-child td{border-bottom:0}.job-state{font-weight:750}.job-state.completed{color:var(--ok)}.job-state.failed{color:var(--bad)}.job-state.running,.job-state.claimed,.job-state.queued{color:var(--warn)}.job-target{font-weight:750}.job-target.dev{color:var(--accent)}.job-target.prod{color:var(--prod)}.jobs-empty{padding:14px;color:var(--muted)}
.logs{margin-top:14px}.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:10px 0 8px}.tab.active{border-color:#397168;background:#17332f}
pre{white-space:pre-wrap;word-break:break-word;background:#080d10;border:1px solid var(--line);padding:12px;border-radius:10px;max-height:310px;overflow:auto;color:#cbd8da}
.toast{position:sticky;bottom:14px;margin:14px auto 0;max-width:720px;padding:10px 14px;border-radius:10px;background:#172228;border:1px solid var(--line);display:none}.toast.show{display:block}.toast.ok{border-color:#2b6c49}.toast.bad{border-color:#74383e}
.lock{padding:8px 10px;background:#151727;border:1px solid #30355f;border-radius:9px;color:#bfc5ff;font-size:12px}
.mode{padding:3px 8px;border-radius:999px;border:1px solid var(--line);font-size:12px}.mode.maintenance{background:#3a3019;border-color:#6e5928;color:#f2c96d}
@media(max-width:900px){.topgrid,.targets{grid-template-columns:1fr}.kv{grid-template-columns:115px minmax(0,1fr)}}
</style>
</head>
<body>
<header><div><div class="brand"><b>EZS</b> ORCHESTRATOR</div><div class="sub">Control Center R3.15 - local uniquement - 127.0.0.1:8700</div></div><div class="sub" id="updated">-</div></header>
<main>
<div id="analysisBanner" class="banner">Etat d'execution en cours de lecture...</div>
<section class="topgrid">
<article class="card"><h2>Service permanent</h2><div class="statusrow"><span id="serviceDot" class="dot"></span><span id="serviceState">-</span></div><div class="big" id="serviceTarget">-</div><div class="muted" id="serviceMeta">-</div><div class="actions"><button id="serviceStart" class="primary">Demarrer service DEV + PROD</button><button id="serviceStop">Arreter service</button></div></article>
<article class="card"><h2>GPU / execution</h2><div class="statusrow"><span id="gpuDot" class="dot"></span><span id="gpuState">-</span></div><div class="big">1 slot GPU</div><div class="muted">Singleton machine-wide protege.</div></article>
<article class="card"><h2>Politique de surete</h2><div class="lock">PROD - exploitation protegee. Seules les operations lifecycle/maintenance sont autorisees.</div><div class="muted" style="margin-top:10px">Code, DB et storage metier restent isoles. Le diagnostic n'exporte jamais ces donnees.</div></article>
</section>
<section class="targets">
<article class="card target dev"><h2>DEV</h2><div class="statusrow"><span id="devDot" class="dot"></span><strong id="devState">-</strong></div><dl class="kv"><dt>Root</dt><dd id="devRoot">-</dd><dt>APP_ENV</dt><dd id="devEnv">-</dd><dt>Backend</dt><dd id="devBackend">-</dd><dt>Caddy</dt><dd id="devCaddy">-</dd><dt>Transport</dt><dd id="devTransport">-</dd><dt>Python analyse</dt><dd id="devPython">-</dd><dt>Ownership</dt><dd id="devOwnership">-</dd></dl><div class="actions"><button data-action="dev-server-start" class="primary">Demarrer backend</button><button data-action="dev-server-restart">Redemarrer backend</button><button data-action="dev-server-stop" data-destructive="1" class="danger">Arreter backend</button><button data-action="dev-caddy-start">Demarrer Caddy</button><a class="btn primary" href="http://127.0.0.1:8502/fr/catalog" target="_blank" rel="noreferrer">Ouvrir DEV</a></div><div class="queue"><span class="muted">Queue DEV</span><br><strong id="devQueue">-</strong></div></article>
<article class="card target prod"><h2>PROD - exploitation protegee</h2><div class="statusrow"><span id="prodDot" class="dot"></span><strong id="prodState">-</strong><span id="prodMode" class="mode">-</span></div><dl class="kv"><dt>Root</dt><dd id="prodRoot">-</dd><dt>APP_ENV</dt><dd id="prodEnv">prod</dd><dt>Backend :8511</dt><dd id="prodBackend">-</dd><dt>Gateway :8510</dt><dd id="prodGateway">-</dd><dt>Caddy :8501</dt><dd id="prodCaddy">-</dd><dt>Transport</dt><dd id="prodTransport">-</dd><dt>Python analyse</dt><dd id="prodPython">-</dd><dt>Ownership backend</dt><dd id="prodOwnership">-</dd></dl><div class="actions"><button data-action="prod-start" class="primary">Demarrer PROD</button><button data-action="prod-restart" data-destructive="1">Redemarrer PROD</button><button data-action="prod-stop" data-destructive="1" class="danger">Arreter PROD</button><button data-action="prod-maintenance-off">Mode normal</button><button data-action="prod-maintenance-on" class="warn">Maintenance</button><a class="btn primary" href="https://ezscore.logandplay.com/fr/catalog" target="_blank" rel="noreferrer">Ouvrir PROD</a></div><div class="queue"><span class="muted">Queue PROD</span><br><strong id="prodQueue">-</strong></div></article>
</section>
<section class="card jobs-panel">
<div class="jobs-head"><h2 style="margin:0">Jobs recents</h2><span class="muted" id="jobsMeta">Chargement...</span></div>
<div class="jobs-table-wrap"><table class="jobs-table">
<thead><tr><th>Job</th><th>Cible</th><th>Type</th><th>Etat</th><th>Date</th><th>RC</th><th>Erreur</th></tr></thead>
<tbody id="jobsBody"><tr><td colspan="7" class="jobs-empty">Chargement...</td></tr></tbody>
</table></div>
</section>
<section class="card logs">
<h2>Logs recents</h2>
<div class="actions"><button id="clearLogs" class="danger">Clear logs</button><button id="exportLogs" class="primary">Export logs ZIP</button></div>
<div class="tabs"><button class="tab active" data-log="service">Service</button><button class="tab" data-log="service_error">Service erreurs</button><button class="tab" data-log="control_center">Control Center</button><button class="tab" data-log="control_center_error">Control Center erreurs</button><button class="tab" data-log="dev_server_error">Backend DEV</button><button class="tab" data-log="dev_caddy_error">Caddy DEV</button><button class="tab" data-log="prod_server_error">Backend PROD</button><button class="tab" data-log="prod_gateway_error">Gateway PROD</button><button class="tab" data-log="prod_caddy_error">Caddy PROD</button></div>
<pre id="logText">Chargement...</pre>
</section>
<div id="toast" class="toast" role="status" aria-live="polite"></div>
</main>
<script>
const TOKEN="__TOKEN__";
let currentLog="service";
let busy=false;
let analysisActive=false;
let refreshInFlight=false;
let devFailures=0;
let prodFailures=0;

const $=id=>document.getElementById(id);
function dot(el,ok,warn=false){el.className="dot "+(ok?"ok":warn?"warn":"bad")}
function txt(id,v){$(id).textContent=v??"-"}
async function getJSON(url){const r=await fetch(url,{cache:"no-store"});if(!r.ok)throw new Error(await r.text());return r.json()}
function toast(message,ok=true){const el=$("toast");el.textContent=message;el.className="toast show "+(ok?"ok":"bad");setTimeout(()=>{el.className="toast"},4500)}
function fmtProc(v){return `pid ${v.pid??'-'} - ${v.process_alive?'PROCESS OK':'PROCESS OFF'} - ${v.http_alive?'HTTP OK':'HTTP OFF'}`}

function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;","\\\"":"&quot;","'":"&#39;"}[c]))}
function renderJobs(payload){
  const body=$("jobsBody"), jobs=(payload&&payload.jobs)||[];
  txt("jobsMeta",payload&&payload.ok?`${payload.count??jobs.length} job(s) · lecture seule`:"Erreur");
  if(!jobs.length){body.innerHTML='<tr><td colspan="7" class="jobs-empty">Aucun job recent.</td></tr>';return;}
  body.innerHTML=jobs.map(j=>{
    const state=String(j.state||'unknown').toLowerCase(), target=String(j.target||'-').toLowerCase();
    return `<tr><td><strong>#${esc(j.job_id)}</strong></td><td><span class="job-target ${esc(target)}">${esc(target.toUpperCase())}</span></td><td>${esc(j.kind||'-')}</td><td><span class="job-state ${esc(state)}">${esc(state.toUpperCase())}</span></td><td>${esc(j.timestamp||'-')}</td><td>${esc(j.returncode??'-')}</td><td>${j.error?esc(j.error):'-'}</td></tr>`;
  }).join('');
}
let jobsRefreshInFlight=false;
async function refreshJobs(){
  if(jobsRefreshInFlight)return;
  jobsRefreshInFlight=true;
  try{renderJobs(await getJSON('/api/jobs'))}
  catch(e){txt("jobsMeta","Erreur de lecture")}
  finally{jobsRefreshInFlight=false}
}

function syncActionButtons(){
  document.querySelectorAll('button[data-action]').forEach(b=>{
    const destructive=b.dataset.destructive==="1";
    b.disabled=busy || (destructive && analysisActive);
  });
}

function render(s){
  analysisActive=!!s.analysis_active;
  txt("updated",`${s.at} · snapshot ${s.snapshot_ms??'-'} ms`);
  const banner=$("analysisBanner");
  banner.textContent=analysisActive?"ANALYSE ACTIVE - stop/restart serveur bloques":"Aucune analyse active";
  banner.className="banner "+(analysisActive?"active":"");
  dot($("gpuDot"),!analysisActive,analysisActive);
  txt("gpuState",analysisActive?"OCCUPE":"LIBRE");

  const svc=s.service||{};
  dot($("serviceDot"),!!svc.running);
  txt("serviceState",svc.running?"RUNNING":"STOPPED");
  txt("serviceTarget",svc.target?String(svc.target).toUpperCase():"-");
  txt("serviceMeta",`pid=${svc.pid??'-'} · state=${svc.state??'-'} · heartbeat=${svc.heartbeat??'-'}`);
  $("serviceStart").disabled=busy||!!svc.running;
  $("serviceStop").disabled=busy||!svc.running;

  const d=s.dev,ds=d.server,dc=d.caddy;
  const devHealthy=!!(ds.process_alive&&ds.http_alive&&dc.process_alive&&dc.http_alive);
  devFailures=devHealthy?0:devFailures+1;
  const devShownOnline=devHealthy||devFailures<3;
  dot($("devDot"),devShownOnline,!devHealthy);
  txt("devState",devHealthy?"ONLINE":(devFailures<3?"DEGRADED / CHECKING":"PROCESS / HTTP DOWN"));
  txt("devRoot",ds.root);txt("devEnv",ds.app_env);
  txt("devBackend",`:${ds.backend_port} - ${fmtProc(ds)}`);
  txt("devCaddy",`:${dc.public_port} - ${fmtProc(dc)}`);
  txt("devTransport",d.transport);txt("devPython",d.analysis_python);
  txt("devOwnership",ds.ownership);
  txt("devQueue",d.queue.ok?`${d.queue.count} job(s)`:"ERROR");

  const p=s.prod,pl=p.lifecycle,pb=pl.backend,pg=pl.gateway,pc=pl.caddy;
  const prodHealthy=!!pl.online;
  prodFailures=prodHealthy?0:prodFailures+1;
  const prodShownOnline=prodHealthy||prodFailures<3;
  dot($("prodDot"),prodShownOnline,!prodHealthy);
  txt("prodState",prodHealthy?"ONLINE":(prodFailures<3?"DEGRADED / CHECKING":"CHAIN INCOMPLETE / DOWN"));
  txt("prodRoot",pb.root);
  txt("prodBackend",`:${pb.backend_port} - ${fmtProc(pb)}`);
  txt("prodGateway",`:${pg.port} - pid ${pg.pid??'-'} - ${pg.process_alive?'PROCESS OK':'PROCESS OFF'} - ${pg.http_alive?'HTTP OK':'HTTP OFF'} - ${pg.protocol??'-'} - ownership=${pg.ownership}`);
  txt("prodCaddy",`:${pc.public_port} - ${fmtProc(pc)}`);
  txt("prodTransport",p.transport);txt("prodPython",p.analysis_python);
  txt("prodOwnership",pb.ownership);
  txt("prodQueue",p.queue.ok?`${p.queue.count} job(s)`:"ERROR");
  const mode=$("prodMode");mode.textContent=(pl.mode||"-").toUpperCase();mode.className="mode "+(pl.mode==="maintenance"?"maintenance":"");
  syncActionButtons();
}

async function refresh(){
  if(refreshInFlight)return;
  refreshInFlight=true;
  try{
    render(await getJSON('/api/status'));
    await refreshLogs();
  }catch(e){
    toast(String(e),false);
  }finally{
    refreshInFlight=false;
  }
}

async function refreshLogs(){
  try{
    const logs=await getJSON('/api/logs');
    const lines=logs[currentLog]||[];
    $("logText").textContent=lines.length?lines.join('\\n'):"(vide)";
  }catch(e){
    $("logText").textContent=String(e);
  }
}

async function action(name){
  if(busy)return;
  busy=true;
  syncActionButtons();
  try{
    const r=await fetch('/api/action',{
      method:'POST',
      headers:{'Content-Type':'application/json','X-EZS-Token':TOKEN},
      body:JSON.stringify({action:name})
    });
    const data=await r.json();
    toast(data.message||data.error||'OK',!!data.ok);
  }catch(e){
    toast(String(e),false);
  }finally{
    busy=false;
    await refresh();
  }
}

document.querySelectorAll('button[data-action]').forEach(b=>b.addEventListener('click',()=>action(b.dataset.action)));
$("serviceStart").addEventListener('click',()=>action('service-start-all'));
$("serviceStop").addEventListener('click',()=>action('service-stop'));

$("clearLogs").addEventListener('click',async()=>{
  if(!confirm("Masquer l'historique actuel des logs ? Les fichiers actifs ne seront pas tronques et aucun serveur/worker ne sera arrete."))return;
  await action('logs-clear');
  await refreshLogs();
});

$("exportLogs").addEventListener('click',async()=>{
  try{
    const r=await fetch('/api/logs/export',{method:'POST',headers:{'X-EZS-Token':TOKEN}});
    if(!r.ok)throw new Error(await r.text());
    const blob=await r.blob();
    const disposition=r.headers.get('Content-Disposition')||'';
    const match=disposition.match(/filename="?([^";]+)"?/);
    const link=document.createElement('a');
    link.href=URL.createObjectURL(blob);
    link.download=match?match[1]:'EZS_orchestrator_logs.zip';
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(()=>URL.revokeObjectURL(link.href),1000);
  }catch(e){
    toast(String(e),false);
  }
});

document.querySelectorAll('.tab').forEach(b=>b.addEventListener('click',()=>{
  document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));
  b.classList.add('active');
  currentLog=b.dataset.log;
  refreshLogs();
}));

refresh();
refreshJobs();
setInterval(refresh,3000);
setInterval(refreshJobs,3000);
</script>
</body></html>'''


def make_handler(center: ControlCenter, token: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "EZSControlCenter/3.15"

        def log_message(self, format: str, *args) -> None:
            return

        def _json(self, payload: dict, code: int = 200) -> None:
            data = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self) -> None:
            path = urlparse(self.path).path
            if path == "/":
                body = HTML.replace("__TOKEN__", token).encode("utf-8")
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
            self._json({"ok": False, "error": "not_found"}, 404)

        def do_POST(self) -> None:
            path = urlparse(self.path).path
            if self.headers.get("X-EZS-Token") != token:
                self._json({"ok": False, "error": "forbidden"}, 403)
                return

            if path == "/api/logs/export":
                try:
                    archive = center.log_tools.export_zip()
                    data = archive.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/zip")
                    self.send_header("Content-Disposition", f'attachment; filename="{archive.name}"')
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(data)))
                    self.end_headers()
                    self.wfile.write(data)
                except Exception as exc:
                    self._json({"ok": False, "error": str(exc)}, 500)
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
    parser = argparse.ArgumentParser(prog="EZS_orchestrator visual control center")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if not (1024 <= args.port <= 65535):
        raise SystemExit("port must be between 1024 and 65535")

    center = ControlCenter()
    token = secrets.token_urlsafe(24)
    server = ThreadingHTTPServer((HOST, args.port), make_handler(center, token))
    url = f"http://{HOST}:{args.port}/"
    print(f"EZS_ORCHESTRATOR_CONTROL_CENTER {url}", flush=True)
    print("PROD lifecycle operations enabled under R3.15 protected policy", flush=True)

    if not args.no_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()

    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
