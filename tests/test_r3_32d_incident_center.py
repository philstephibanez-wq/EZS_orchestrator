from __future__ import annotations
import tempfile, unittest
from pathlib import Path
from control_center.incidents import IncidentStore
class Contract(unittest.TestCase):
    def test_persist_ack_resolve(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=IncidentStore(Path(tmp))
            a=s.sync([{"severity":"CRITICAL","code":"foreign_process","source":"lab","message":"foreign","log_key":"lab_server_error"}])
            self.assertEqual(len(a),1)
            iid=a[0]["id"]
            s2=IncidentStore(Path(tmp))
            self.assertEqual(s2.snapshot()[0]["id"],iid)
            self.assertTrue(s2.acknowledge(iid)["acknowledged_at"])
            self.assertEqual(s2.sync([]),[])
            row=next(x for x in s2.snapshot(include_resolved=True) if x["id"]==iid)
            self.assertFalse(row["active"])
            self.assertTrue(row["resolved_at"])
    def test_levels(self):
        with tempfile.TemporaryDirectory() as tmp:
            s=IncidentStore(Path(tmp))
            for level in ("INFO","WARNING","ERROR","CRITICAL"):
                a=s.sync([{"severity":level,"code":"x","source":level,"message":"m"}])
                self.assertEqual(a[0]["severity"],level)
if __name__ == "__main__":
    unittest.main()
