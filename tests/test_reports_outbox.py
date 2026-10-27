import unittest
from unittest.mock import patch
import reports_outbox
class OutboxTests(unittest.TestCase):
 def test_opt_in_required(self):
  with patch.dict("os.environ",{},clear=True):
   self.assertEqual(reports_outbox.drain()["state"],"disabled")
 def test_legacy_blocks(self):
  with patch.dict("os.environ",{"EZS_EVENT_REPORTS_ENABLED":"1"}),patch.object(reports_outbox,"_legacy_active",return_value=True):
   self.assertEqual(reports_outbox.drain()["state"],"legacy_tasks_active")
 def test_no_polling_or_timer(self):
  from pathlib import Path
  src=(Path(__file__).resolve().parents[1]/"reports_outbox.py").read_text()
  self.assertNotIn("sleep(",src)
  self.assertIn("revision_id",src)
