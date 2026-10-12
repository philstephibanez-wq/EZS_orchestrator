from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from service.lab_circuit import LabCircuitBreaker
class Contract(unittest.TestCase):
    def test_three_failures_open_reset(self):
        with tempfile.TemporaryDirectory() as tmp:
            b=LabCircuitBreaker(Path(tmp),threshold=3,cooldown_seconds=60)
            self.assertTrue(b.can_attempt()[0])
            self.assertEqual(b.record_failure("1")["state"],"closed")
            self.assertEqual(b.record_failure("2")["state"],"closed")
            self.assertEqual(b.record_failure("3")["state"],"open")
            self.assertFalse(b.can_attempt()[0])
            b.reset()
            self.assertTrue(b.can_attempt()[0])
if __name__ == "__main__":
    unittest.main()
