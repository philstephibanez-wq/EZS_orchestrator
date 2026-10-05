from pathlib import Path
import ast

root = Path(__file__).resolve().parents[1]
m = (root/"deployment"/"manager.py").read_text(encoding="utf-8-sig")
w = (root/"control_center"/"web.py").read_text(encoding="utf-8-sig")

ast.parse(m)
ast.parse(w)

# V1.0.8 no-op + progress
assert 'reasons.append("already_up_to_date")' in m
assert 'def _progress(' in m
assert 'Progression du déploiement' in w
assert 'DEV et PROD pointent sur le même commit. Aucun déploiement à effectuer.' in w

# V1.0.8a readable history
for needle in (
    'def _commit_metadata(',
    '"commit_subject": commit_meta.get("subject")',
    '"commit_author": commit_meta.get("author_name")',
    'const subject=x.commit_subject||',
    'const author=x.commit_author||"Auteur inconnu"',
):
    assert needle in (m + w), needle

print("EZS_ORCHESTRATOR_V1_0_8A_DEPLOY_UX_OK")
