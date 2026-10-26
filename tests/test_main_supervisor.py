import unittest
from unittest.mock import patch
from assistant_supervision.main_supervisor import MainSupervisor, docker

class MainDockerSupervisorTest(unittest.TestCase):
    def test_health_uses_cuda_health_endpoint(self):
        lines='{"Names":"ezstudio-assistant-main-smoke-assistant-web-smoke-1"}\n{"Names":"ezstudio-assistant-main-cuda-llama-cuda-smoke-1"}\n'
        with patch("assistant_supervision.main_supervisor.docker", return_value=lines), patch("assistant_supervision.main_supervisor.ready", return_value=True) as check:
            result=MainSupervisor().status()
        self.assertEqual(result["state"],"ONLINE")
        check.assert_any_call(18720, "/health")

    def test_error_exposed_without_restarting_services(self):
        with patch("assistant_supervision.main_supervisor.docker", side_effect=RuntimeError("missing docker")):
            result=MainSupervisor().status()
        self.assertEqual(result["state"],"ERROR")
        self.assertIn("missing docker",result["error"])

    def test_docker_fallback_executable(self):
        with patch("assistant_supervision.main_supervisor.shutil.which",return_value=None), patch("pathlib.Path.is_file",return_value=True), patch("assistant_supervision.main_supervisor.subprocess.run") as run:
            run.return_value.returncode=0
            run.return_value.stdout=""
            docker(["ps"])
            self.assertTrue(run.call_args.args[0][0].replace(chr(92), "/").lower().endswith("/docker/desktop/resources/bin/docker.exe"))
if __name__=="__main__":
    unittest.main()
