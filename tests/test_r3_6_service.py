from __future__ import annotations

import tempfile
import unittest
import uuid
from pathlib import Path

from service.runner import PermanentRunner
from service.singleton import ServiceSingleton, ServiceSingletonBusy


class R36ServiceTest(unittest.TestCase):
    def setUp(self):
        # Windows uses a machine-wide named mutex. Unit tests must never contend
        # with the real permanent Orchestrator service already running on the host.
        self._original_mutex_name = ServiceSingleton.WINDOWS_MUTEX_NAME
        ServiceSingleton.WINDOWS_MUTEX_NAME = (
            rf"Global\EZS_orchestrator_service_test_{uuid.uuid4().hex}"
        )

    def tearDown(self):
        ServiceSingleton.WINDOWS_MUTEX_NAME = self._original_mutex_name

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


if __name__ == "__main__":
    unittest.main()
