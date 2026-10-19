"""R27B: source contracts for Infrastructure and fail-closed deployment.
Does not contact XPS or start any server.
"""
from __future__ import annotations
import ast
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]

class R27BContracts(unittest.TestCase):
    def test_infrastructure_polling_visibility_and_error_state(self):
        src = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8-sig")
        self.assertRegex(src, r"(?:setInterval|setTimeout)\s*\(")
        self.assertIn("visibilitychange", src)
        self.assertIn("document.hidden", src)
        self.assertIn("5000", src)
        self.assertIn('"/api/status"', src)
        self.assertIn("refreshInFlight", src)
        # Refresh must remain a GET; no service action in its own body.
        start = src.index("async function refresh()")
        end = src.index("async function action(", start)
        fragment = src[start:end]
        self.assertNotIn('method:"POST"', fragment)
        self.assertNotIn('/api/action', fragment)

    def test_profile_runtime_has_canonical_preset_and_local_ai(self):
        src = (ROOT / "assistant_supervision" / "remote_helper.ps1").read_text(encoding="utf-8-sig")
        self.assertIn("R20_PROFILE_AI_FROM_CANONICAL_CACHE_MANIFEST", src)
        self.assertIn("EZSTUDIOLAB_REVIEW_PRESET_PATH", src)
        self.assertIn("EZAssistantPresets", src)
        self.assertIn("EZSTUDIOLAB_AI_PROVIDER", src)
        self.assertIn("127.0.0.1:8720", src)

    def test_deploy_is_fail_closed_before_side_effects(self):
        src = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8-sig")
        tree = ast.parse(src)
        node = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "deploy")
        self.assertIn("R27B_FAIL_CLOSED_LEGACY_DEPLOY_GUARD", src)
        self.assertIsInstance(node.body[0], ast.Raise)
        raises = [n for n in node.body if isinstance(n, ast.Raise)]
        self.assertTrue(raises, "fail-closed raise must be top-level and unconditional")
        first_call = next((n for n in node.body if isinstance(n, ast.Expr) and isinstance(n.value, ast.Call)), None)
        if first_call:
            self.assertLess(raises[0].lineno, first_call.lineno)
        self.assertIn("r27_profile_safe_handover_not_implemented", ast.get_source_segment(src, raises[0]))

    def test_scientific_and_runtime_assets_untouched(self):
        src = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8-sig")
        self.assertIn("DEFAULT_LAB_ROOT", src)
        self.assertIn("DEFAULT_SOURCE", src)
