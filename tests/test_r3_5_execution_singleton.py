from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from runtime_guard.singleton import (
    ExecutionSingleton,
    ExecutionSingletonBusy,
)


class R35ExecutionSingletonTest(unittest.TestCase):
    def test_second_instance_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = ExecutionSingleton(root)
            b = ExecutionSingleton(root)

            a.acquire(target="dev", job_id=131)
            try:
                with self.assertRaises(ExecutionSingletonBusy):
                    b.acquire(target="prod", job_id=99)
            finally:
                a.release()

    def test_lock_can_be_reacquired_after_release(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            a = ExecutionSingleton(root)
            b = ExecutionSingleton(root)

            a.acquire(target="dev")
            a.release()

            b.acquire(target="prod")
            self.assertTrue(b.held)
            b.release()

    def test_metadata_is_removed_on_release(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            lock = ExecutionSingleton(root)
            lock.acquire(target="dev", job_id=131)
            self.assertTrue(lock.meta_path.is_file())
            lock.release()
            self.assertFalse(lock.meta_path.exists())


if __name__ == "__main__":
    unittest.main()
