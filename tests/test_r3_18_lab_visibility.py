from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parents[1]
web = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
ast.parse(web)

assert '"lab": {' in web
assert 'self._queue(Target.LAB)' in web
assert 'analysis_python_for(Target.LAB)' in web
assert 'transport_url_for(Target.LAB)' in web
assert 'Queue LAB' in web
assert 'labQueueCount' in web
assert 'labQueueList' in web
assert 'labQueueMeta' in web
assert 'Démarrer service DEV + PROD + LAB' in web

history = (ROOT / "control_center" / "job_history.py").read_text(encoding="utf-8")
assert '("dev", "prod", "lab")' in history

runner = (ROOT / "service" / "runner.py").read_text(encoding="utf-8")
assert '(Target.DEV, Target.PROD, Target.LAB)' in runner

cli = (ROOT / "control_center" / "cli.py").read_text(encoding="utf-8")
assert 'choices=("dev", "prod", "lab")' in cli

print("EZS_ORCHESTRATOR_LAB_VISIBILITY_R3_18_CONTRACT_OK")
