from __future__ import annotations
import ast, json, pathlib, unittest
from unittest.mock import patch
from types import SimpleNamespace
import assistant_deployment.manager as m
ROOT=pathlib.Path(__file__).resolve().parents[1]
class R27CProfileReadOnlyPreflight(unittest.TestCase):
    def plan(self):
        return m.DeployPlan(source='x',source_commit='a'*40,parent_gitlink_commit='a'*40,node='example',remote_root=r'C:\EZStudioLab_assistant',remote_host_repo=r'C:\EZStudioLab_assistant\runtime')
    def test_legacy_deploy_still_blocked(self):
        src=(ROOT/'assistant_deployment'/'manager.py').read_text(encoding='utf-8-sig')
        f=next(n for n in ast.parse(src).body if isinstance(n,ast.FunctionDef) and n.name=='deploy')
        self.assertIsInstance(f.body[0],ast.Raise)
        with self.assertRaisesRegex(RuntimeError,'r27_profile_safe_handover_not_implemented'):m.deploy(self.plan())
    def test_remote_inventory_has_no_mutation(self):
        x={'schema':'ezs.r27c.profile-preflight.v1','profile_pids':[20132],'ai_pids':[54],'opaque_processes':[],'profile_task_present':True,'profile_task_state':'Ready'}
        with patch.object(m,'_run_remote_lifecycle_script',return_value=SimpleNamespace(returncode=0,stdout=json.dumps(x))) as call:
            result=m.profile_remote_preflight(self.plan())
        script=call.call_args.args[1]
        for forbidden in ('Stop-Process','Stop-ScheduledTask','Unregister-ScheduledTask','Remove-Item','Start-ScheduledTask'):
            self.assertNotIn(forbidden,script)
        self.assertFalse(result['safe_to_use_legacy_deploy'])
        self.assertIn('profile_worker_active',result['blockers'])
    def test_inventory_failure_is_fail_closed(self):
        with patch.object(m,'_run_remote_lifecycle_script',return_value=SimpleNamespace(returncode=1,stdout='')):
            with self.assertRaisesRegex(RuntimeError,'r27c_remote_inventory_unavailable'):m.profile_remote_preflight(self.plan())
        with patch.object(m,'_run_remote_lifecycle_script',return_value=SimpleNamespace(returncode=0,stdout='{}')):
            with self.assertRaisesRegex(RuntimeError,'r27c_remote_inventory_invalid'):m.profile_remote_preflight(self.plan())
    def test_only_manager_and_new_tests(self):
        self.assertIn('R27C_READ_ONLY_PROFILE_REMOTE_PREFLIGHT',(ROOT/'assistant_deployment'/'manager.py').read_text(encoding='utf-8-sig'))
