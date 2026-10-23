"""Tests contractuels du dispatch existant (sans réseau)."""
from __future__ import annotations
import unittest
from unittest.mock import patch
from contracts.job import JobEnvelope
from contracts.target import Target
from orchestration.profile_dispatch import dispatch, KEYS

class DispatchTests(unittest.TestCase):
    def test_refuses_non_lab(self):
        job=JobEnvelope(job_id=1,target=Target.DEV,kind="assistant.profile.review")
        with self.assertRaisesRegex(ValueError,"unsupported_dispatch_job"):
            dispatch(job,None,xps_url="http://xps")
    def test_refuses_empty_payload(self):
        job=JobEnvelope(job_id=1,target=Target.LAB,kind="assistant.profile.review")
        with self.assertRaisesRegex(ValueError,"profile_payload_required"):
            dispatch(job,None,xps_url="http://xps")
    def test_keys_are_ten(self):
        self.assertEqual(len(KEYS),10)

if __name__=="__main__":
    unittest.main()
