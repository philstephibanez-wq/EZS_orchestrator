import unittest
from unittest.mock import patch
from reports_review_event import publish_completed_revision
class ReviewEventTests(unittest.TestCase):
 def test_disabled_by_default(self):
  with patch.dict("os.environ",{},clear=True):
   self.assertEqual(publish_completed_revision(1)["reason"],"not_enabled")
 def test_rejects_bad_id(self):
  with self.assertRaises(ValueError): publish_completed_revision(0)
 def test_refuses_to_publish_backlog(self):
  from pathlib import Path
  code=(Path(__file__).resolve().parents[1]/"reports_review_event.py").read_text()
  self.assertIn("requires_targeted_summary_publisher",code)
  self.assertNotIn('"--once"',code)
