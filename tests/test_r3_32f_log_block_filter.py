from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from control_center.log_tools import LogTools


class Contract(unittest.TestCase):
    def test_full_control_center_block_is_suppressed(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            path = root / "logs" / "control-center-error.log"
            path.parent.mkdir(parents=True)
            path.write_text(
                "----------------------------------------\n"
                "Exception occurred during processing of request "
                "from ('127.0.0.1', 54206)\n"
                "Traceback (most recent call last):\n"
                "  File \"x.py\", line 1, in x\n"
                "ConnectionAbortedError: [WinError 10053] host aborted\n"
                "\n"
                "During handling of the above exception, "
                "another exception occurred:\n"
                "\n"
                "Traceback (most recent call last):\n"
                "  File \"y.py\", line 2, in y\n"
                "ConnectionAbortedError: [WinError 10053] host aborted\n"
                "----------------------------------------\n",
                encoding="utf-8",
            )
            self.assertEqual(LogTools(root).error_alerts(), [])


if __name__ == "__main__":
    unittest.main()
