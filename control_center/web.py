from __future__ import annotations

import argparse
import json
import secrets
import subprocess
import sys
import threading
import webbrowser
from dataclasses import asdict
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from caddy_manager.manager import CaddyManager
from config.loader import load_runtime_config
from contracts.target import Target
from runtime_guard.activity import analysis_execution_active
from server_manager.manager import ServerManager
from transport.jobs import JobTransport
from transport.targets import TargetRegistry

HOST = "127.0.0.1"
DEFAULT_PORT = 8700

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
        self.transport = JobTransport(TargetRegistry(self.config))
        self.action_lock = threading.Lock()

    @property
    def runtime(self) -> Path:
        return self.config.orchestrator_root / "runtime"

    def _service_status(self) -> dict:
        service_dir = self.runtime / "service"
        meta = _read_json(service_dir / "service.json")
        heartbeat = _read_json(service_dir / "heartbeat.json")
        if not meta:
            return {"running": False, "pid": None, "target": None, "poll_seconds": None, "state": "stopped", "heartbeat": None}
        return {"running": True, "pid": meta.get("pid"), "target": meta.get("target"), "poll_seconds": meta.get("poll_seconds"), "state": heartbeat.get("state", "unknown"), "heartbeat": heartbeat.get("at")}

    def _queue(self, target: Target) -> dict:
        try:
            jobs = self.transport.queue(target)
            return {"ok": True, "count": len(jobs), "jobs": jobs[:8]}
        except Exception as exc:
            return {"ok": False, "count": None, "jobs": [], "error": str(exc)}

    def snapshot(self) -> dict:
        dev = self.servers.view(Target.DEV)
        prod = self.servers.view(Target.PROD)
        dev_caddy = self.caddy.view(Target.DEV)
        prod_caddy = self.caddy.view(Target.PROD)
        return {
            "at": datetime.now(timezone.utc).isoformat(),
            "analysis_active": bool(analysis_execution_active(self.runtime)),
            "service": self._service_status(),
            "dev": {"server": asdict(dev), "caddy": asdict(dev_caddy), "queue": self._queue(Target.DEV), "analysis_python": str(self.config.analysis_python_for(Target.DEV)), "transport": self.config.transport_url_for(Target.DEV)},
            "prod": {"server": asdict(prod), "caddy": asdict(prod_caddy), "queue": self._queue(Target.PROD), "analysis_python": str(self.config.analysis_python_for(Target.PROD)), "transport": self.config.transport_url_for(Target.PROD)},
        }

    def action(self, name: str) -> dict:
        with self.action_lock:
            if name == "dev-server-start":
                view = self.servers.start(Target.DEV)
                return {"ok": True, "message": f"DEV server started/adopted pid={view.pid}"}
            if name == "dev-server-stop":
                view = self.servers.stop(Target.DEV)
                return {"ok": True, "message": "DEV server stopped" if not view.process_alive else "DEV server still active"}
            if name == "dev-server-restart":
                view = self.servers.restart(Target.DEV)
                return {"ok": True, "message": f"DEV server restarted pid={view.pid}"}
            if name == "dev-caddy-start":
                view = self.caddy.start(Target.DEV)
                return {"ok": True, "message": f"DEV Caddy active pid={view.pid}"}
            if name == "service-start-dev":
                service_dir = self.runtime / "service"
                if (service_dir / "service.json").is_file():
                    return {"ok": True, "message": "Orchestrator service already active"}
                completed = subprocess.run([sys.executable, "-m", "service.service_cli", "start", "--target", "dev", "--poll-seconds", "2"], cwd=str(self.config.orchestrator_root), capture_output=True, text=True, timeout=10)
                output = (completed.stdout or completed.stderr).strip()
                return {"ok": completed.returncode == 0, "message": output or f"returncode={completed.returncode}"}
            if name == "service-stop":
                completed = subprocess.run([sys.executable, "-m", "service.service_cli", "stop", "--wait-seconds", "15"], cwd=str(self.config.orchestrator_root), capture_output=True, text=True, timeout=20)
                output = (completed.stdout or completed.stderr).strip()
                return {"ok": completed.returncode == 0, "message": output or f"returncode={completed.returncode}"}
            raise ValueError(f"unsupported_action:{name}")

    def logs(self) -> dict:
        root = self.config.orchestrator_root
        return {
            "service": _tail(root / "runtime" / "service" / "service.out.log"),
            "service_error": _tail(root / "runtime" / "service" / "service.err.log"),
            "dev_server_error": _tail(root / "logs" / "servers" / "dev.err.log"),
            "dev_caddy_error": _tail(root / "runtime" / "caddy" / "dev" / "caddy.err.log"),
        }

HTML = '<!doctype html>\n<html lang="fr">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n<title>EZS Orchestrator - Control Center</title>\n<style>\n:root{color-scheme:dark;--bg:#0b1114;--panel:#111a1f;--panel2:#162229;--line:#26363f;--text:#ecf5f4;--muted:#93a8ad;--accent:#49d1bd;--ok:#5ed38b;--warn:#f2c96d;--bad:#ff7b7b;--prod:#98a5ff}\n*{box-sizing:border-box}body{margin:0;font:14px/1.45 system-ui,Segoe UI,Arial;background:var(--bg);color:var(--text)}\nheader{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 24px;border-bottom:1px solid var(--line);background:#0d1519}\n.brand{font-weight:800;letter-spacing:.04em;font-size:18px}.brand b{color:var(--accent)}.sub{color:var(--muted);font-size:12px}\nmain{padding:20px;max-width:1500px;margin:auto}.topgrid{display:grid;grid-template-columns:1.2fr 1fr 1fr;gap:14px;margin-bottom:14px}\n.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;min-width:0}.card h2{margin:0 0 12px;font-size:14px}\n.statusrow{display:flex;align-items:center;gap:9px;flex-wrap:wrap}.dot{width:10px;height:10px;border-radius:50%;background:var(--muted);display:inline-block}.dot.ok{background:var(--ok)}.dot.warn{background:var(--warn)}.dot.bad{background:var(--bad)}\n.big{font-size:22px;font-weight:750;margin:6px 0}.muted{color:var(--muted)}.targets{display:grid;grid-template-columns:1fr 1fr;gap:14px}.target.dev{border-top:3px solid var(--accent)}.target.prod{border-top:3px solid var(--prod)}\n.kv{display:grid;grid-template-columns:140px minmax(0,1fr);gap:7px 10px;margin:10px 0}.kv dt{color:var(--muted)}.kv dd{margin:0;overflow-wrap:anywhere}\n.actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:14px}button,a.btn{appearance:none;border:1px solid var(--line);background:var(--panel2);color:var(--text);border-radius:9px;padding:9px 12px;text-decoration:none;cursor:pointer;font-weight:650}\nbutton.primary,a.primary{background:#173b37;border-color:#27655d}button.danger{background:#371d21;border-color:#6f343c}button:disabled{opacity:.45;cursor:not-allowed}\n.queue{margin-top:14px;border-top:1px solid var(--line);padding-top:12px}.queue strong{font-size:19px}.banner{margin-bottom:14px;padding:11px 14px;border:1px solid var(--line);border-radius:10px;background:var(--panel)}.banner.active{border-color:#775a27;background:#251f13}\n.logs{margin-top:14px}.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px}.tab.active{border-color:#397168;background:#17332f}\npre{white-space:pre-wrap;word-break:break-word;background:#080d10;border:1px solid var(--line);padding:12px;border-radius:10px;max-height:310px;overflow:auto;color:#cbd8da}\n.toast{position:sticky;bottom:14px;margin:14px auto 0;max-width:720px;padding:10px 14px;border-radius:10px;background:#172228;border:1px solid var(--line);display:none}.toast.show{display:block}.toast.ok{border-color:#2b6c49}.toast.bad{border-color:#74383e}\n.lock{padding:8px 10px;background:#151727;border:1px solid #30355f;border-radius:9px;color:#bfc5ff;font-size:12px}\n@media(max-width:900px){.topgrid,.targets{grid-template-columns:1fr}.kv{grid-template-columns:110px minmax(0,1fr)}}\n</style>\n</head>\n<body>\n<header>\n  <div><div class="brand"><b>EZS</b> ORCHESTRATOR</div><div class="sub">Control Center - local uniquement - 127.0.0.1:8700</div></div>\n  <div class="sub" id="updated">-</div>\n</header>\n<main>\n  <div id="analysisBanner" class="banner">Etat d\'execution en cours de lecture...</div>\n  <section class="topgrid">\n    <article class="card">\n      <h2>Service permanent</h2>\n      <div class="statusrow"><span id="serviceDot" class="dot"></span><span id="serviceState">-</span></div>\n      <div class="big" id="serviceTarget">-</div>\n      <div class="muted" id="serviceMeta">-</div>\n      <div class="actions">\n        <button id="serviceStart" class="primary">Demarrer service DEV</button>\n        <button id="serviceStop">Arreter service</button>\n      </div>\n    </article>\n    <article class="card">\n      <h2>GPU / execution</h2>\n      <div class="statusrow"><span id="gpuDot" class="dot"></span><span id="gpuState">-</span></div>\n      <div class="big">1 slot GPU</div>\n      <div class="muted">Singleton machine-wide protege.</div>\n    </article>\n    <article class="card">\n      <h2>Politique de surete</h2>\n      <div class="lock">PROD est volontairement en lecture seule dans cette interface R3.9.</div>\n      <div class="muted" style="margin-top:10px">Aucune action visuelle ne peut demarrer, arreter ou redemarrer PROD.</div>\n    </article>\n  </section>\n  <section class="targets">\n    <article class="card target dev">\n      <h2>DEV</h2>\n      <div class="statusrow"><span id="devDot" class="dot"></span><strong id="devState">-</strong></div>\n      <dl class="kv">\n        <dt>Root</dt><dd id="devRoot">-</dd><dt>APP_ENV</dt><dd id="devEnv">-</dd><dt>Backend</dt><dd id="devBackend">-</dd>\n        <dt>Caddy</dt><dd id="devCaddy">-</dd><dt>Transport</dt><dd id="devTransport">-</dd><dt>Python analyse</dt><dd id="devPython">-</dd><dt>Ownership</dt><dd id="devOwnership">-</dd>\n      </dl>\n      <div class="actions">\n        <button data-action="dev-server-start" class="primary">Demarrer backend</button>\n        <button data-action="dev-server-restart">Redemarrer backend</button>\n        <button data-action="dev-server-stop" class="danger">Arreter backend</button>\n        <button data-action="dev-caddy-start">Demarrer Caddy</button>\n        <a class="btn primary" href="http://127.0.0.1:8502/fr/catalog" target="_blank" rel="noreferrer">Ouvrir DEV</a>\n      </div>\n      <div class="queue"><span class="muted">Queue DEV</span><br><strong id="devQueue">-</strong></div>\n    </article>\n    <article class="card target prod">\n      <h2>PROD - lecture seule</h2>\n      <div class="statusrow"><span id="prodDot" class="dot"></span><strong id="prodState">-</strong></div>\n      <dl class="kv">\n        <dt>Root</dt><dd id="prodRoot">-</dd><dt>APP_ENV</dt><dd id="prodEnv">-</dd><dt>Backend</dt><dd id="prodBackend">-</dd>\n        <dt>Gateway</dt><dd id="prodGateway">-</dd><dt>Caddy</dt><dd id="prodCaddy">-</dd><dt>Transport</dt><dd id="prodTransport">-</dd><dt>Python analyse</dt><dd id="prodPython">-</dd><dt>Ownership</dt><dd id="prodOwnership">-</dd>\n      </dl>\n      <div class="queue"><span class="muted">Queue PROD</span><br><strong id="prodQueue">-</strong></div>\n    </article>\n  </section>\n  <section class="card logs">\n    <h2>Logs recents</h2>\n    <div class="tabs">\n      <button class="tab active" data-log="service">Service</button><button class="tab" data-log="service_error">Service erreurs</button>\n      <button class="tab" data-log="dev_server_error">Backend DEV</button><button class="tab" data-log="dev_caddy_error">Caddy DEV</button>\n    </div>\n    <pre id="logText">Chargement...</pre>\n  </section>\n  <div id="toast" class="toast" role="status" aria-live="polite"></div>\n</main>\n<script>\nconst TOKEN="__TOKEN__";let currentLog="service";let busy=false;\nconst $=id=>document.getElementById(id);function dot(el,ok,warn=false){el.className="dot "+(ok?"ok":warn?"warn":"bad")}function txt(id,v){$(id).textContent=v??"-"}\nasync function getJSON(url){const r=await fetch(url,{cache:"no-store"});if(!r.ok)throw new Error(await r.text());return r.json()}\nfunction toast(message,ok=true){const el=$("toast");el.textContent=message;el.className="toast show "+(ok?"ok":"bad");setTimeout(()=>{el.className="toast"},4500)}\nfunction renderTarget(prefix,t,prod){const sv=t.server,ca=t.caddy,up=sv.process_alive&&sv.http_alive;dot($(prefix+"Dot"),up);txt(prefix+"State",up?"ONLINE":(sv.process_alive?"PROCESS / HTTP DOWN":"STOPPED"));txt(prefix+"Root",sv.root);txt(prefix+"Env",sv.app_env);txt(prefix+"Backend",`:${sv.backend_port} - pid ${sv.pid||"-"} - HTTP ${sv.http_alive?"OK":"OFF"}`);if(prod)txt("prodGateway",sv.gateway_port?":"+sv.gateway_port:"-");txt(prefix+"Caddy",`:${ca.public_port} - pid ${ca.pid||"-"} - HTTP ${ca.http_alive?"OK":"OFF"}`);txt(prefix+"Transport",t.transport);txt(prefix+"Python",t.analysis_python);txt(prefix+"Ownership",sv.ownership);txt(prefix+"Queue",t.queue.ok?`${t.queue.count} job(s)`:"ERREUR")}\nasync function refresh(){try{const s=await getJSON("/api/status");txt("updated","Actualise "+new Date(s.at).toLocaleTimeString());const svc=s.service;dot($("serviceDot"),svc.running);txt("serviceState",svc.running?("running / "+svc.state):"stopped");txt("serviceTarget",svc.running?("target="+svc.target):"Service arrete");txt("serviceMeta",svc.running?`PID ${svc.pid} - poll ${svc.poll_seconds}s - heartbeat ${svc.heartbeat||"-"}`:"Aucun processus permanent");$("serviceStart").disabled=svc.running||busy;$("serviceStop").disabled=!svc.running||busy;dot($("gpuDot"),!s.analysis_active,s.analysis_active);txt("gpuState",s.analysis_active?"Analyse en cours":"Libre");const b=$("analysisBanner");b.textContent=s.analysis_active?"ANALYSE ACTIVE - stop/restart backend proteges par le guard R3.7.":"Aucune analyse active.";b.className="banner"+(s.analysis_active?" active":"");renderTarget("dev",s.dev,false);renderTarget("prod",s.prod,true)}catch(e){toast("Erreur status: "+e.message,false)}}\nasync function action(name){if(busy)return;busy=true;document.querySelectorAll("button[data-action]").forEach(b=>b.disabled=true);try{const r=await fetch("/api/action",{method:"POST",headers:{"Content-Type":"application/json","X-EZS-Token":TOKEN},body:JSON.stringify({action:name})});const data=await r.json();toast(data.message||name,!!data.ok)}catch(e){toast("Action en echec: "+e.message,false)}finally{busy=false;await refresh();document.querySelectorAll("button[data-action]").forEach(b=>b.disabled=false)}}\nasync function refreshLog(){try{const l=await getJSON("/api/logs");$("logText").textContent=(l[currentLog]||[]).join("\\n")||"(vide)"}catch(e){$("logText").textContent="Erreur lecture logs: "+e.message}}\ndocument.querySelectorAll("button[data-action]").forEach(b=>b.addEventListener("click",()=>action(b.dataset.action)));$("serviceStart").addEventListener("click",()=>action("service-start-dev"));$("serviceStop").addEventListener("click",()=>action("service-stop"));document.querySelectorAll(".tab").forEach(b=>b.addEventListener("click",()=>{document.querySelectorAll(".tab").forEach(x=>x.classList.remove("active"));b.classList.add("active");currentLog=b.dataset.log;refreshLog()}));refresh();refreshLog();setInterval(refresh,2000);setInterval(refreshLog,4000);\n</script>\n</body>\n</html>'

def make_handler(center: ControlCenter, token: str):
    class Handler(BaseHTTPRequestHandler):
        server_version = "EZSControlCenter/3.9"
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
            if path == "/api/logs":
                self._json(center.logs())
                return
            self._json({"ok": False, "error": "not_found"}, 404)
        def do_POST(self) -> None:
            if urlparse(self.path).path != "/api/action":
                self._json({"ok": False, "error": "not_found"}, 404)
                return
            if self.headers.get("X-EZS-Token") != token:
                self._json({"ok": False, "error": "forbidden"}, 403)
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
    print("PROD mutations: disabled (read-only policy R3.9)", flush=True)
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
