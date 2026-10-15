from __future__ import annotations

import inspect
import unittest

import caddy_manager.manager as caddy_manager
import control_center.web as control_center_web
import gateway_manager.manager as gateway_manager
import server_manager.manager as server_manager
import transport.jobs as transport_jobs


class RuntimeStateAndProfilerV12kContract(unittest.TestCase):
    def test_dead_stored_pid_is_not_reported_foreign(self):
        self.assertIn(
            "stored_pid if pid_alive(stored_pid) else None",
            inspect.getsource(server_manager.ServerManager.view),
        )
        self.assertIn(
            "stored if self._pid_alive(stored) else None",
            inspect.getsource(caddy_manager.CaddyManager.view),
        )
        self.assertIn(
            "stored if pid_alive(stored) else None",
            inspect.getsource(gateway_manager.GatewayManager.view),
        )

    def test_queue_incident_requires_live_backend(self):
        source = inspect.getsource(control_center_web.ControlCenter._safety_status)
        self.assertIn("backend_alive", source)
        self.assertIn("if backend_alive and queue.get(\"ok\") is False:", source)

    def test_queue_poll_disables_dev_profiler_collection(self):
        source = inspect.getsource(transport_jobs.JobTransport.queue)
        self.assertIn("?_ezs_profile=0", source)


if __name__ == "__main__":
    unittest.main()
