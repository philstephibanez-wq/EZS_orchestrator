from __future__ import annotations
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def replace_once(path:Path, old:str, new:str)->None:
    text=path.read_text(encoding="utf-8")
    if new in text:
        return
    if old not in text:
        raise RuntimeError(f"{path}: migration anchor absent")
    path.write_text(text.replace(old,new,1),encoding="utf-8",newline="\n")

def main()->int:
    planner=ROOT/"executor"/"planner.py"
    replace_once(
        planner,
        "        if target is Target.LAB and self.config.lab is not None:\n"
        "            return self.config.lab.root\n",
        "        lab = getattr(self.config, \"lab\", None)\n"
        "        if target is Target.LAB and lab is not None:\n"
        "            return lab.root\n",
    )
    replace_once(
        planner,
        "        roots = [self.config.dev.root, self.config.prod.root]\n"
        "        if self.config.lab is not None:\n"
        "            roots.append(self.config.lab.root)\n",
        "        roots = [self.config.dev.root, self.config.prod.root]\n"
        "        lab = getattr(self.config, \"lab\", None)\n"
        "        if lab is not None:\n"
        "            roots.append(lab.root)\n",
    )
    replace_once(
        planner,
        "            configured = self.config.lab_analysis_python\n",
        "            configured = getattr(self.config, \"lab_analysis_python\", None)\n",
    )

    # Historical fixture was stale against current production signature.
    # Production service.py already calls executor.run(..., on_progress=...).
    test=ROOT/"tests"/"test_r3_2_explicit_target.py"
    replace_once(
        test,
        "    def run(self, job, on_output=None):\n"
        "        return self.R()\n",
        "    def run(self, job, on_output=None, on_progress=None):\n"
        "        return self.R()\n",
    )

    print("EZS_ORCHESTRATOR_LAB_R3_17B_HOTFIX_MIGRATION_OK")
    print("EZS_ORCHESTRATOR_LEGACY_TEST_FIXTURE_COMPAT_OK")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
