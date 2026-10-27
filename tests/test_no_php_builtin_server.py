import inspect
import unittest

from server_manager.manager import ServerManager
from contracts.target import Target


class NoPhpHttpServerContract(unittest.TestCase):
    def test_no_builtin_server_launch(self):
        source = inspect.getsource(ServerManager.start)
        self.assertNotIn('"-S"', source)
        self.assertIn('php_builtin_server_forbidden', source)

    def test_all_targets_fail_closed(self):
        manager = object.__new__(ServerManager)
        for target in (Target.DEV, Target.PROD, Target.LAB):
            with self.subTest(target=target):
                with self.assertRaisesRegex(RuntimeError, 'php_builtin_server_forbidden'):
                    manager.start(target)


if __name__ == '__main__':
    unittest.main()
