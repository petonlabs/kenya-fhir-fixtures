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



class ArchitectureSafetyTests(unittest.TestCase):
    """Metamorphic tests that fail if the detector only compares output labels."""

    def test_same_threshold_category_different_evidence_is_not_equivalent(self):
        from comparison import compare
        a, b = base_pair()
        b["lab"]["number"] = "6.9"
        ca, cb = canonical("fhir", a), canonical("legacy", b)
        da, db = decide(ca), decide(cb)
        self.assertEqual(da.clinical, db.clinical)
        axes = compare(ca, cb, da, db)["axes"]
        self.assertFalse(axes["evidence"])
        self.assertTrue(axes["clinical_decision"])

    def test_duplicate_observation_abstains_instead_of_last_wins(self):
        a, _ = base_pair()
        a["bundle"]["entry"].append(copy.deepcopy(a["bundle"]["entry"][2]))
        ctx = canonical("fhir", a)
        self.assertIn("FHIR_RESOURCE_CARDINALITY_OBSERVATION", ctx["adapter_issues"])
        self.assertEqual("ABSTAIN", decide(ctx).clinical)

    def test_duplicate_patient_abstains(self):
        a, _ = base_pair()
        a["bundle"]["entry"].append(copy.deepcopy(a["bundle"]["entry"][0]))
        self.assertEqual("ABSTAIN", decide(canonical("fhir", a)).clinical)

    def test_multicode_input_requires_explicit_mapping_choice(self):
        a, _ = base_pair()
        a["bundle"]["entry"][2]["resource"]["code"]["coding"].append(
            {"system": "https://example.org/local", "code": "Hb"})
        ctx = canonical("fhir", a)
        self.assertIn("FHIR_CODING_AMBIGUOUS_OR_MISSING", ctx["adapter_issues"])
        self.assertEqual("ABSTAIN", decide(ctx).clinical)

    def test_ucum_system_ambiguity_abstains(self):
        a, _ = base_pair()
        a["bundle"]["entry"][2]["resource"]["valueQuantity"]["system"] = "https://example.org/units"
        self.assertIn("FHIR_UCUM_SYSTEM_UNVERIFIED", decide(canonical("fhir", a)).reasons)

    def test_missing_quantity_abstains(self):
        a, _ = base_pair()
        del a["bundle"]["entry"][2]["resource"]["valueQuantity"]
        self.assertEqual("ABSTAIN", decide(canonical("fhir", a)).clinical)

    def test_timezones_same_instant_are_equivalent(self):
        from comparison import compare
        a, b = base_pair()
        b["lab"]["collected_at"] = "2026-11-20T05:30:00+00:00"
        ca, cb = canonical("fhir", a), canonical("legacy", b)
        self.assertTrue(compare(ca, cb, decide(ca), decide(cb))["equivalent"])

    def test_consent_difference_does_not_mutate_clinical_recommendation(self):
        from comparison import compare
        a, b = base_pair()
        b["workflow"]["consent_to_message"] = False
        ca, cb = canonical("fhir", a), canonical("legacy", b)
        axes = compare(ca, cb, decide(ca), decide(cb))["axes"]
        self.assertTrue(axes["clinical_decision"])
        self.assertTrue(axes["evidence"])
        self.assertFalse(axes["communication_authorization"])
        self.assertFalse(axes["workflow_context"])

    def test_scenario_report_contains_all_six_axes(self):
        result = run()
        self.assertTrue(result["summary"]["all_expectations_met"])
        names = {"evidence", "clinical_decision", "communication_authorization",
                 "reason_codes", "workflow_context", "rule_identity"}
        for case in result["cases"]:
            self.assertEqual(names, set(case["comparison"]["axes"]))
            if case["expected_relation"] == "same":
                self.assertEqual([], case["comparison"]["discrepancy_axes"])

    def test_missing_fhir_bundle_fails_closed(self):
        a, _ = base_pair()
        del a["bundle"]
        self.assertEqual("ABSTAIN", decide(canonical("fhir", a)).clinical)

if __name__ == '__main__':
    unittest.main()
