from __future__ import annotations
import unittest
from pathlib import Path
from assistant_deployment.manager import DeployPlan, _remote_script

ROOT=Path(__file__).resolve().parents[1]
MANAGER=(ROOT/"assistant_deployment"/"manager.py").read_text(encoding="utf-8")
WEB=(ROOT/"control_center"/"web.py").read_text(encoding="utf-8")

class V12PAssistantDeployTransactionContract(unittest.TestCase):
    def plan(self):
        return DeployPlan(source=r"H:\EZStudioLab_assistant",source_commit="a"*40,parent_gitlink_commit="a"*40,node="steph@example",remote_root=r"C:\EZStudioLab_assistant",remote_host_repo=r"C:\EZStudioLab_assistant\runtime")
    def test_staging_validated_before_ai_stop(self):
        r=_remote_script(self.plan(),"runtime.zip")
        self.assertLess(r.index("assistant_staging_not_clean"),r.index("Stop-Process -Id $localAIPid"))
    def test_ai_intent_marker_before_swap(self):
        r=_remote_script(self.plan(),"runtime.zip")
        self.assertIn("assistant-deploy-state.json",r); self.assertIn("local_ai_was_running",r)
        self.assertLess(r.index("assistant-deploy-state.json"),r.index("[System.IO.Directory]::Move($remoteRoot, $previous)"))
    def test_deploy_call_is_inside_transaction_try(self):
        s=WEB.index("    def assistant_deployment_apply(self) -> dict:"); tail=WEB[s:]; n=tail.find("\n    def ",10); m=tail if n<0 else tail[:n]
        self.assertLess(m.index("            try:"),m.index("deploy_assistant_node(plan)"))
        self.assertLess(m.index("deploy_assistant_node(plan)"),m.index("            except Exception as exc:"))
    def test_finalize_requires_expected_ai_health(self):
        self.assertIn("assistant_finalize_local_ai_not_healthy",MANAGER)
    def test_rollback_recovers_ai_intent(self):
        self.assertIn("$rollbackAIWasRunning = [bool]$deployState.local_ai_was_running",MANAGER)
        self.assertIn("assistant_rollback_no_previous_recovered_current_root",MANAGER)
        self.assertIn("assistant_rollback_local_ai_restart_health_timeout",MANAGER)

if __name__=="__main__": unittest.main()
