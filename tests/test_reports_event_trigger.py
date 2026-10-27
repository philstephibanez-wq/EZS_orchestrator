import unittest
from unittest.mock import patch
from reports_control import notify_completed
class TriggerTest(unittest.TestCase):
 def test_disabled_by_default(self):
  with patch.dict("os.environ",{},clear=True):
   self.assertEqual(notify_completed(job_id=1,kind="profile",target="lab")["reason"],"not_enabled")
 def test_no_report_on_expertise_dispatch(self):
  with patch.dict("os.environ",{"EZS_EVENT_REPORTS_ENABLED":"1"}):
   self.assertEqual(notify_completed(job_id=1,kind="assistant.profile.review",target="lab")["reason"],"not_final_lab_analysis")
 def test_no_report_on_non_lab(self):
  self.assertEqual(notify_completed(job_id=1,kind="profile",target="dev")["status"],"skipped")
