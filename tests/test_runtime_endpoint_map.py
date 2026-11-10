import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('endpoint_map',ROOT/'scripts/runtime_endpoint_map.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

class RuntimeEndpointMapTest(unittest.TestCase):
    def test_config_and_manifest_contract(self):
        config,manifest=MODULE.load(ROOT)
        self.assertEqual('ezs.runtime.endpoints.v1',manifest['schema'])
        self.assertEqual('ezs.orchestrator.config.v5',config['schema'])
        self.assertEqual(3,len(config['servers']))

    def test_canonical_routes_are_not_mutating_probes(self):
        _,manifest=MODULE.load(ROOT)
        self.assertTrue(all(p['method']=='GET' for p in manifest['probes']))
        self.assertFalse(any('/cancel' in p['path'] or '/delete' in p['path'] for p in manifest['probes']))

    def test_proxy_port_contract(self):
        config,_=MODULE.load(ROOT)
        for name in ('dev','prod','lab'):
            cfg_text=(ROOT/'config/frankenphp'/('Caddyfile.'+name+'.native')).read_text(encoding='utf-8-sig')
            ports=config['servers'][name]
            for key in ('public_port','backend_port'):
                self.assertIn('127.0.0.1:'+str(ports[key]),cfg_text)
            if name=='prod':
                self.assertIn('127.0.0.1:'+str(ports['gateway_port']),cfg_text)
                self.assertIn('/internal/media/auth',cfg_text)

    def test_endpoint_manifest_without_secrets(self):
        source=(ROOT/'docs/endpoints.v1.json').read_text(encoding='utf-8')
        for bad in ('OPENAI_API_KEY','LAB_TOKEN','Bearer ','password'):
            self.assertNotIn(bad,source)

if __name__=='__main__':
    unittest.main()
