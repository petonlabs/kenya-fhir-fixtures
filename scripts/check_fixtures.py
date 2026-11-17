#!/usr/bin/env python3
"""Offline catalog/fixture preflight only: NOT HL7 FHIR conformance validation."""
import copy
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]


def inspect(root=ROOT):
    manifest = json.loads((root / 'manifest.json').read_text())
    assert manifest['ig']['package_id'] == 'ke.fhir.core'
    assert manifest['ig']['version'] == '1.0.0'
    cases = manifest['fixtures']
    assert len(cases) == 12
    assert {c['resourceType'] for c in cases} == {'Patient','Encounter','ServiceRequest'}
    assert len({c['id'] for c in cases}) == len(cases)
    loaded = {}
    for c in cases:
        file = (root / c['file']).resolve()
        assert file.is_relative_to(root.resolve())
        assert file.exists(), c['file']
        v = json.loads(file.read_text())
        assert v['resourceType'] == c['resourceType'], c['id']
        assert v['meta']['profile'] == [c['profile']], c['id']
        assert v['id'].startswith('synthetic-'), c['id']
        loaded[c['id']] = v
    assert sum(c['expected']=='pass' for c in cases)==6
    assert sum(c['expected']=='fail' for c in cases)==6
    for c in cases:
        if c['expected']!='fail': continue
        positive = copy.deepcopy(loaded[c['negative_of']])
        negative = copy.deepcopy(loaded[c['id']])
        negative['id'] = positive['id'] # id is intentionally distinct; ignore it for one mutation
        # Each negative = its positive with exactly the declared single-field mutation.
        mut = c['mutation']
        assert len(mut) == 1 and (len(mut.get('remove', 'x').split()) == 1), c['id']
        if 'remove' in mut:
            assert mut['remove'] in positive and mut['remove'] not in negative, c['id']
            positive.pop(mut['remove'])
        else:
            (field, value), = mut['set'].items()
            assert positive[field] != value, c['id']
            positive[field] = value
        assert c['expected_errors'], c['id']
        assert positive==negative, c['id']
    return len(cases)

if __name__=='__main__':
    print(f'Integrity preflight OK: {inspect()} candidate fixture files (NOT FHIR-validated).')
