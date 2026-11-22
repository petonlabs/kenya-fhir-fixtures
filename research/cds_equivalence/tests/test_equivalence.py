import copy
import hashlib
import json
import unittest

from equivalence import POLICY, base_pair, canonical, decide, digest, run, scenarios


class EquivalenceTests(unittest.TestCase):
    def test_scenario_count_and_classification(self):
        cases = scenarios()
        self.assertEqual(len(cases), 12)
        self.assertEqual(sum(c['expected'] == 'same' for c in cases), 4)
        self.assertEqual(sum(c['expected'] == 'different' for c in cases), 8)

    def test_expected_outcomes(self):
        report = run()
        self.assertTrue(report['summary']['all_expectations_met'])
        self.assertEqual(report['summary']['drifts_detected'], 8)

    def test_result_is_deterministic(self):
        self.assertEqual(digest(run()), digest(run()))

    def test_canonical_equivalent_distinct_inputs(self):
        a, b = base_pair()
        af, bf = canonical('fhir', a), canonical('legacy', b)
        self.assertEqual(af['facts']['hb_g_dl'], bf['facts']['hb_g_dl'])
        self.assertEqual(decide(af).clinical, decide(bf).clinical)
        self.assertNotEqual(af['provenance']['source_hash_sha256'], bf['provenance']['source_hash_sha256'])

    def test_unit_normalization(self):
        a, b = base_pair()
        b['lab'].update(number='68', uom='g/L')
        self.assertEqual(canonical('legacy', b)['facts']['hb_g_dl'], '6.8')

    def test_malformed_unit_abstains(self):
        _, b = base_pair()
        b['lab']['uom'] = 'mmol/L'
        out = decide(canonical('legacy', b))
        self.assertEqual(out.clinical, 'ABSTAIN')
        self.assertEqual(out.communication, 'BLOCKED')

    def test_preliminary_abstains(self):
        a, _ = base_pair()
        a['bundle']['entry'][2]['resource']['status'] = 'preliminary'
        self.assertIn('RESULT_NOT_FINAL', decide(canonical('fhir', a)).reasons)

    def test_person_mismatch_abstains(self):
        _, b = base_pair()
        b['lab']['patient_key'] = 'pat-999'
        self.assertIn('PATIENT_REFERENCE_CONFLICT', decide(canonical('legacy', b)).reasons)

    def test_wrong_encounter_is_blocked(self):
        a, b = base_pair()
        a['bundle']['entry'][2]['resource']['encounter']['reference'] = 'Encounter/other'
        b['lab']['visit_key'] = 'other'
        self.assertIn('ENCOUNTER_REFERENCE_CONFLICT', decide(canonical('fhir', a)).reasons)
        self.assertIn('ENCOUNTER_REFERENCE_CONFLICT', decide(canonical('legacy', b)).reasons)

    def test_consent_changes_only_communication(self):
        _, b = base_pair()
        approved = decide(canonical('legacy', b))
        b['workflow']['consent_to_message'] = False
        denied = decide(canonical('legacy', b))
        self.assertEqual(approved.clinical, denied.clinical)
        self.assertEqual(denied.communication, 'BLOCKED')

    def test_unverified_identity_blocks_clinical(self):
        _, b = base_pair()
        b['workflow']['identity_verified'] = False
        self.assertEqual(decide(canonical('legacy', b)).clinical, 'ABSTAIN')

    def test_nonadult_scope_abstains(self):
        a, _ = base_pair()
        a['workflow']['age_years'] = 17
        self.assertEqual(decide(canonical('fhir', a)).clinical, 'ABSTAIN')

    def test_unavailable_pregnancy_status_abstains(self):
        a, _ = base_pair()
        a['workflow']['pregnant'] = None
        self.assertEqual(decide(canonical('fhir', a)).clinical, 'ABSTAIN')

    def test_future_timestamp_abstains(self):
        _, b = base_pair()
        b['lab']['collected_at'] = '2027-01-01T10:00:00+03:00'
        self.assertIn('FUTURE_RESULT', decide(canonical('legacy', b)).reasons)

    def test_policy_version_and_hash_in_report(self):
        report = run()
        self.assertEqual(report['policy_hash_sha256'], digest(POLICY))
        self.assertIn('training-only', report['policy']['version'])

    def test_source_immutability(self):
        a, b = base_pair()
        before = (digest(a), digest(b))
        decide(canonical('fhir', a))
        decide(canonical('legacy', b))
        self.assertEqual(before, (digest(a), digest(b)))


if __name__ == '__main__':
    unittest.main()
