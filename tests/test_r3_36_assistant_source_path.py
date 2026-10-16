from pathlib import Path
import py_compile
import unittest

ROOT = Path(__file__).resolve().parents[1]
WEB = (ROOT / "control_center" / "web.py").read_text(encoding="utf-8")
DEPLOY = (ROOT / "assistant_deployment" / "manager.py").read_text(encoding="utf-8")


class R336AssistantSourcePathContract(unittest.TestCase):
    def test_version_remains_1_2m(self):
        self.assertEqual(
            "1.2m",
            (ROOT / "VERSION").read_text(encoding="utf-8-sig").strip(),
        )

    def test_operational_code_uses_independent_assistant_repo(self):
        expected = r"H:\EZStudioLab_assistant"
        forbidden = r"H:\EZStudio_lab\EZStudioLab_assistant"
        self.assertIn(expected, WEB)
        self.assertIn(expected, DEPLOY)
        self.assertNotIn(forbidden, WEB)
        self.assertNotIn(forbidden, DEPLOY)

    def test_lab_root_remains_separate_for_scientific_runtime_dependencies(self):
        self.assertIn(r'DEFAULT_LAB_ROOT = Path(r"H:\EZStudio_lab")', DEPLOY)
        self.assertIn(r'DEFAULT_SOURCE = Path(r"H:\EZStudioLab_assistant")', DEPLOY)

    def test_parent_gitlink_is_no_longer_required(self):
        self.assertNotIn("assistant_parent_gitlink_missing", DEPLOY)
        self.assertNotIn("assistant_source_not_parent_pinned", DEPLOY)
        self.assertIn("parent_gitlink_commit=source_commit", DEPLOY)

    def test_modified_python_compiles(self):
        py_compile.compile(str(ROOT / "control_center" / "web.py"), doraise=True)
        py_compile.compile(str(ROOT / "assistant_deployment" / "manager.py"), doraise=True)


if __name__ == "__main__":
    unittest.main()
