import json
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from check_fixtures import inspect

class FixtureIntegrityTests(unittest.TestCase):
    def test_candidate_cases(self):
        self.assertEqual(inspect(ROOT),12)
    def test_all_resources_use_synthetic_placeholders(self):
        manifest=json.loads((ROOT/'manifest.json').read_text())
        for case in manifest['fixtures']:
            resource=json.loads((ROOT/case['file']).read_text())
            self.assertTrue(resource['id'].startswith('synthetic-'))
            self.assertIn('https://fhir.dha.go.ke/core/StructureDefinition/',resource['meta']['profile'][0])

if __name__=='__main__': unittest.main()
