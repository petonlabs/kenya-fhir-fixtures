import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from run_validator import messages, targeted

class OperationOutcomeContractTests(unittest.TestCase):
    def test_extracts_error(self):
        outcome={'resourceType':'OperationOutcome','issue':[{'severity':'error','code':'invariant','diagnostics':'sha-patient-min-identifier violated','expression':['Patient.identifier']}]}
        rows=messages(outcome)
        self.assertEqual(len(rows),1)
        self.assertTrue(targeted(rows[0][1],{'expected_constraint':'sha-patient-min-identifier','expected_path':'Patient.identifier'}))
    def test_unrelated_error_is_not_intended(self):
        self.assertFalse(targeted('Encounter.class is missing',{'expected_constraint':'min-cardinality','expected_path':'Encounter.subject'}))
    def test_unknown_response_fails_closed(self):
        with self.assertRaises(ValueError): messages({'resourceType':'Bundle','entry':[]})

if __name__=='__main__':unittest.main()
