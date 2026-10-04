from __future__ import annotations

import unittest

from config.loader import load_runtime_config
from contracts.job import JobEnvelope
from contracts.target import Target
from executor.planner import ExecutionPlanner


class R31CompatibilityContractTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config = load_runtime_config()
        cls.planner = ExecutionPlanner(cls.config)

    def test_legacy_payload_is_accepted_but_not_serialized(self):
        job = JobEnvelope(
            101,
            Target.DEV,
            "stems",
            payload={"paths": {"source": r"H:\EZScore_dev\var\storage\ok.wav"}},
        )
        payload = job.to_dict()
        self.assertNotIn("payload", payload)

    def test_legacy_payload_cross_root_is_rejected(self):
        job = JobEnvelope(
            102,
            Target.DEV,
            "stems",
            payload={"paths": {"source": r"H:\EZScore\var\storage\bad.wav"}},
        )
        with self.assertRaises(RuntimeError):
            self.planner.plan(job)

    def test_v2_paths_cross_root_is_rejected(self):
        job = JobEnvelope(
            103,
            Target.PROD,
            "lyrics",
            paths={"source": r"H:\EZScore_dev\var\storage\bad.wav"},
        )
        with self.assertRaises(RuntimeError):
            self.planner.plan(job)

    def test_structured_v2_is_authoritative_serialization(self):
        job = JobEnvelope(
            104,
            Target.DEV,
            "chords",
            paths={"source": r"H:\EZScore_dev\var\storage\song.wav"},
            request={"level": "intermediate"},
            payload={"legacy": "ignored_for_serialization"},
        )
        data = job.to_dict()
        self.assertEqual(
            data["paths"]["source"],
            r"H:\EZScore_dev\var\storage\song.wav",
        )
        self.assertEqual(data["request"]["level"], "intermediate")
        self.assertNotIn("payload", data)


if __name__ == "__main__":
    unittest.main()
