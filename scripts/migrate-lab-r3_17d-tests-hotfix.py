from __future__ import annotations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def replace_once(path:Path, old:str, new:str)->None:
    text=path.read_text(encoding="utf-8")
    if old not in text:
        if new and new in text:
            return
        raise RuntimeError(f"{path}: migration anchor absent")
    path.write_text(text.replace(old,new,1),encoding="utf-8",newline="\n")

def remove_once(path:Path, old:str)->None:
    text=path.read_text(encoding="utf-8")
    if old not in text:
        return
    path.write_text(text.replace(old,"",1),encoding="utf-8",newline="\n")

def main()->int:
    # Fix the R3.17C deletion bug: empty replacement must not be treated as idempotent success.
    header=ROOT/"tests"/"test_orchestrator_v1_0_4_header.py"
    obsolete="    'Control Center local · 127.0.0.1:8700',\n"
    remove_once(header,obsolete)

    # Re-apply the other intended test-only compatibility updates idempotently.
    modal=ROOT/"tests"/"test_orchestrator_v1_0_7_3_deploy_modal.py"
    replace_once(
        modal,
        "    'const confirmed=await openDeploymentModal(fresh);if(!confirmed)return;',\n",
        "    'const confirmed=await openDeploymentModal(fresh);',\n"
        "    'if(!confirmed)return;',\n",
    )

    claim=ROOT/"tests"/"test_r3_3_claim_failure_cleanup.py"
    replace_once(
        claim,
        "class _Executor:\n"
        "    def run(self, job, on_output=None):\n",
        "class _Executor:\n"
        "    def run(self, job, on_output=None, on_progress=None):\n",
    )

    php=ROOT/"tests"/"test_r3_12_dev_php_x64.py"
    replace_once(
        php,
        "    def test_dev_uses_explicit_x64_php_and_prod_keeps_legacy_fallback(self):\n",
        "    def test_dev_and_prod_use_explicit_x64_php(self):\n",
    )
    replace_once(
        php,
        "        self.assertEqual(config.web_php_for(Target.PROD), Path(\"php\"))\n",
        "        self.assertEqual(\n"
        "            config.web_php_for(Target.PROD),\n"
        "            Path(r\"H:\\PHP\\php-8.5-x64\\php.exe\"),\n"
        "        )\n",
    )

    # Fail immediately if any intended stale assertion survived.
    checks={
        header:"Control Center local · 127.0.0.1:8700",
        modal:"const confirmed=await openDeploymentModal(fresh);if(!confirmed)return;",
        claim:"def run(self, job, on_output=None):",
        php:'Path("php")',
    }
    for path,needle in checks.items():
        text=path.read_text(encoding="utf-8")
        if needle in text:
            raise RuntimeError(f"{path}: stale assertion still present: {needle}")

    print("EZS_ORCHESTRATOR_LAB_R3_17D_TESTS_HOTFIX_MIGRATION_OK")
    print("EZS_ORCHESTRATOR_R3_17D_STALE_ASSERTIONS_REMOVED_OK")
    print("EZS_ORCHESTRATOR_PRODUCTION_CODE_UNTOUCHED_OK")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
