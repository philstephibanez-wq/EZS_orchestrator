from __future__ import annotations
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=(ROOT/"server_manager"/"process.py").read_text(encoding="utf-8")
class Contract(unittest.TestCase):
    def test_handle_prototypes(self):
        self.assertIn("OpenProcess.restype = wintypes.HANDLE",P)
        self.assertIn("CloseHandle.argtypes = [wintypes.HANDLE]",P)
        self.assertIn("QueryFullProcessImageNameW.argtypes",P)
        self.assertIn("GetProcessTimes.argtypes",P)
        self.assertIn("GetProcessMemoryInfo.argtypes",P)
if __name__=="__main__": unittest.main()
