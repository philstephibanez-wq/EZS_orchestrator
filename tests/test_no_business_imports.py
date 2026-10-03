from __future__ import annotations

import unittest
from pathlib import Path


class NoBusinessImportsTest(unittest.TestCase):
    def test_scheduler_has_no_analysis_business_terms(self):
        root = Path(__file__).resolve().parents[1]
        scheduler_text = "\n".join(
            p.read_text(encoding="utf-8", errors="replace")
            for p in (root / "scheduler").glob("*.py")
        ).lower()

        forbidden = (
            "whisper",
            "bs_roformer",
            "mel_band_roformer",
            "lyrics_timeline",
            "chordia",
            "demucs",
        )
        for token in forbidden:
            self.assertNotIn(token, scheduler_text, token)


if __name__ == "__main__":
    unittest.main()
