from __future__ import annotations

import io
import unittest

from service.runner import _safe_stream_write


class R317EUnicodeOutputTest(unittest.TestCase):
    def test_cp1252_stream_survives_replacement_character(self):
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="cp1252", errors="strict", newline="", write_through=True)
        _safe_stream_write(stream, "worker output \ufffd fin\n")
        stream.flush()
        data = raw.getvalue().decode("cp1252")
        self.assertIn(r"\ufffd", data)
        self.assertIn("worker output", data)

    def test_ascii_output_is_unchanged(self):
        raw = io.BytesIO()
        stream = io.TextIOWrapper(raw, encoding="cp1252", errors="strict", newline="", write_through=True)
        _safe_stream_write(stream, "job_id=1 target=lab returncode=0\n")
        stream.flush()
        self.assertEqual(
            raw.getvalue().decode("cp1252"),
            "job_id=1 target=lab returncode=0\n",
        )


if __name__=="__main__":
    unittest.main()
