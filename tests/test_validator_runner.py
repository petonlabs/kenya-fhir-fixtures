import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import run_validator
from run_validator import judge, outcomes, signature

EXT = 'http://hl7.org/fhir/StructureDefinition/operationoutcome-'
PROFILE = 'https://fhir.dha.go.ke/core/StructureDefinition/kenya-core-patient'


def issue(severity, msgid, text='', expression=('Patient',)):
    return {'severity': severity, 'code': 'x', 'details': {'text': text}, 'expression': list(expression),
            'extension': [{'url': EXT + 'message-id', 'valueCode': msgid}]}


MIN_ID = issue('error', 'Validation_VAL_Profile_Minimum', 'Patient.identifier: minimum required = 1, but only found 0')
INV_ID = issue('error', PROFILE + '#sha-patient-min-identifier', 'Constraint failed: sha-patient-min-identifier')
WARN = issue('warning', 'http://hl7.org/fhir/StructureDefinition/DomainResource#dom-6')
CASE = {'expected_errors': ['min:Patient.identifier', 'invariant:sha-patient-min-identifier']}


class SignatureTests(unittest.TestCase):
    def test_min_and_invariant(self):
        self.assertEqual(signature(MIN_ID), 'min:Patient.identifier')
        self.assertEqual(signature(INV_ID), 'invariant:sha-patient-min-identifier')

    def test_unknown_issue_kept_distinct(self):
        self.assertEqual(signature(issue('error', 'Some_Other', expression=['Patient.x'])), 'other:Some_Other@Patient.x')


class JudgeTests(unittest.TestCase):
    def test_exact_match_passes_and_warnings_ignored(self):
        self.assertEqual(judge(CASE, {'issue': [MIN_ID, INV_ID, WARN]})[0], 'PASS')

    def test_positive_with_any_error_fails(self):
        self.assertEqual(judge({'expected_errors': []}, {'issue': [MIN_ID]})[0], 'FAIL')

    def test_right_path_wrong_reason_fails(self):
        wrong = issue('error', 'Type_Mismatch', 'Patient.identifier: wrong type', ['Patient.identifier'])
        self.assertEqual(judge({'expected_errors': ['min:Patient.identifier']}, {'issue': [wrong]})[0], 'FAIL')

    def test_unrelated_extra_error_fails(self):
        extra = issue('error', 'Validation_VAL_Profile_Minimum', 'Patient.name: minimum required = 1')
        self.assertEqual(judge(CASE, {'issue': [MIN_ID, INV_ID, extra]})[0], 'FAIL')

    def test_missing_one_expected_error_fails(self):
        self.assertEqual(judge(CASE, {'issue': [MIN_ID]})[0], 'FAIL')

    def test_warning_only_negative_fails(self):
        warn_inv = issue('warning', PROFILE + '#national-id-format')
        self.assertEqual(judge({'expected_errors': ['invariant:national-id-format']}, {'issue': [warn_inv]})[0], 'FAIL')


class BlockedTests(unittest.TestCase):
    def test_non_operation_outcome_blocked(self):
        with self.assertRaises(ValueError):
            outcomes({'resourceType': 'Bundle', 'entry': [{'resource': {'resourceType': 'Patient'}}]})
        with self.assertRaises(ValueError):
            outcomes({'resourceType': 'Patient'})

    def test_outcome_without_file_blocked(self):
        with self.assertRaises(ValueError):
            outcomes({'resourceType': 'OperationOutcome', 'issue': []})

    def _run(self, *argv):
        with mock.patch.object(sys, 'argv', ['run_validator.py', *argv]), contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as cm:
                run_validator.main()
        return cm.exception.code

    def test_missing_artifacts_blocked(self):
        self.assertEqual(self._run('--jar', '/nonexistent.jar', '--ig', '/nonexistent.tgz'), 2)

    def test_unpinned_artifact_blocked(self):
        with tempfile.TemporaryDirectory() as tmp:
            jar, ig = Path(tmp) / 'validator_cli.jar', Path(tmp) / 'ke.fhir.core.tgz'
            jar.write_bytes(b'not the pinned jar')
            ig.write_bytes(b'not the pinned package')
            self.assertEqual(self._run('--jar', str(jar), '--ig', str(ig)), 2)


if __name__ == '__main__':
    unittest.main()
