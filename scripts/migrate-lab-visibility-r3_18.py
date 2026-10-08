from __future__ import annotations

from pathlib import Path
import os
import tempfile

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "control_center" / "web.py"
source = PATH.read_text(encoding="utf-8-sig")

if '"lab": {' in source and 'labQueueCount' in source:
    print("EZS_ORCHESTRATOR_LAB_VISIBILITY_R3_18_ALREADY_APPLIED")
    raise SystemExit(0)

def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected exactly one anchor, found {count}")
    return text.replace(old, new, 1)

old_snapshot = '''            "prod": {
                "lifecycle": prod.as_dict(),
                "queue": self._queue(Target.PROD),
                "analysis_python": str(self.config.analysis_python_for(Target.PROD)),
                "transport": self.config.transport_url_for(Target.PROD),
            },
        }'''

new_snapshot = '''            "prod": {
                "lifecycle": prod.as_dict(),
                "queue": self._queue(Target.PROD),
                "analysis_python": str(self.config.analysis_python_for(Target.PROD)),
                "transport": self.config.transport_url_for(Target.PROD),
            },
            "lab": {
                "queue": self._queue(Target.LAB),
                "analysis_python": str(self.config.analysis_python_for(Target.LAB)),
                "transport": self.config.transport_url_for(Target.LAB),
                "root": str(self.config.lab.root) if self.config.lab is not None else None,
            },
        }'''
source = replace_once(source, old_snapshot, new_snapshot, "snapshot_lab")

source = replace_once(
    source,
    'Démarrer service DEV + PROD',
    'Démarrer service DEV + PROD + LAB',
    "service_label"
)
source = replace_once(
    source,
    'DEV et PROD restent physiquement isolés.',
    'DEV, PROD et LAB restent physiquement isolés.',
    "safety_label"
)

old_cards = '''  <section class="grid2">
    <article class="card queueCard"><h2>Queue DEV</h2><strong id="devQueueCount">-</strong><div id="devQueueList" class="queueList"></div></article>
    <article class="card queueCard"><h2>Queue PROD</h2><strong id="prodQueueCount">-</strong><div id="prodQueueList" class="queueList"></div></article>
  </section>'''

new_cards = '''  <section class="grid3">
    <article class="card queueCard"><h2>Queue DEV</h2><strong id="devQueueCount">-</strong><div id="devQueueList" class="queueList"></div></article>
    <article class="card queueCard"><h2>Queue PROD</h2><strong id="prodQueueCount">-</strong><div id="prodQueueList" class="queueList"></div></article>
    <article class="card queueCard"><h2>Queue LAB</h2><strong id="labQueueCount">-</strong><div id="labQueueList" class="queueList"></div><div class="muted" id="labQueueMeta"></div></article>
  </section>'''
source = replace_once(source, old_cards, new_cards, "lab_queue_card")

old_render = '''txt("prodOwnership",pb.ownership);renderQueue("prodQueueCount","prodQueueList",p.queue);const mode=$("prodMode");mode.textContent=(pl.mode||"-").toUpperCase();mode.className="mode "+(pl.mode==="maintenance"?"maintenance":"");syncActionButtons();'''

new_render = '''txt("prodOwnership",pb.ownership);renderQueue("prodQueueCount","prodQueueList",p.queue);const mode=$("prodMode");mode.textContent=(pl.mode||"-").toUpperCase();mode.className="mode "+(pl.mode==="maintenance"?"maintenance":"");
 const l=s.lab||{};renderQueue("labQueueCount","labQueueList",l.queue);txt("labQueueMeta",`${l.transport??"-"} · ${l.analysis_python??"-"}`);
 syncActionButtons();'''
source = replace_once(source, old_render, new_render, "render_lab_queue")

fd, tmp_name = tempfile.mkstemp(prefix="web.py.", suffix=".tmp", dir=str(PATH.parent))
os.close(fd)
tmp = Path(tmp_name)
try:
    tmp.write_text(source, encoding="utf-8")
    os.replace(tmp, PATH)
finally:
    tmp.unlink(missing_ok=True)

print("EZS_ORCHESTRATOR_LAB_VISIBILITY_R3_18_SOURCE_OK")
