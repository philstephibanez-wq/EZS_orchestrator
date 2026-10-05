from pathlib import Path
import unittest

from config.loader import load_runtime_config
from contracts.target import Target


class DevPhpX64Contract(unittest.TestCase):
    def test_dev_uses_explicit_x64_php_and_prod_keeps_legacy_fallback(self):
        config = load_runtime_config()
        self.assertEqual(
            config.web_php_for(Target.DEV),
            Path(r"H:\PHP\php-8.5-x64\php.exe"),
        )
        self.assertEqual(config.web_php_for(Target.PROD), Path("php"))


if __name__ == "__main__":
    unittest.main()