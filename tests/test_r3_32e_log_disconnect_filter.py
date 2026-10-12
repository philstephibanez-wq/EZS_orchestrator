from __future__ import annotations
import tempfile
import unittest
from pathlib import Path
from control_center.log_tools import LogTools
class Contract(unittest.TestCase):
    def test_benign_disconnect_traceback_is_suppressed(self):
        with tempfile.TemporaryDirectory() as td:
            root=Path(td)
            p=root/"logs"/"control-center-error.log"
            p.parent.mkdir(parents=True)
            p.write_text(
                "Traceback (most recent call last):\n"
                "  File \"x.py\", line 1, in x\n"
                "ConnectionAbortedError: [WinError 10053] software caused connection abort\n",
                encoding="utf-8",
            )
            self.assertEqual(LogTools(root).error_alerts(),[])
if __name__=="__main__": unittest.main()
