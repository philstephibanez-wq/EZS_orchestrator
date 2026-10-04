from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from service.runner import PermanentRunner
from service.singleton import ServiceSingleton, ServiceSingletonBusy


class R36ServiceTest(unittest.TestCase):
    def test_service_singleton_rejects_second_instance(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = ServiceSingleton(root)
            b = ServiceSingleton(root)

            a.acquire(target="dev", poll_seconds=2.0)
            try:
                with self.assertRaises(ServiceSingletonBusy):
                    b.acquire(target="prod", poll_seconds=2.0)
            finally:
                a.release()

    def test_service_lock_reacquires_after_release(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = ServiceSingleton(root)
            b = ServiceSingleton(root)
            a.acquire(target="dev", poll_seconds=2.0)
            a.release()
            b.acquire(target="prod", poll_seconds=2.0)
            self.assertTrue(b.held)
            b.release()

    def test_job_id_extraction(self):
        # Avoid constructing PermanentRunner because it loads real config.
        obj = object.__new__(PermanentRunner)
        self.assertEqual(
            obj._extract_job_id('job_id=131 target=dev returncode=0'),
            131,
        )
        self.assertEqual(
            obj._extract_job_id('{"event":"job_complete","job_id":42}'),
            42,
        )
        self.assertIsNone(obj._extract_job_id("nothing"))
