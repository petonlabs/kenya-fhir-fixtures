#!/usr/bin/env python3
"""Run the pinned HL7 validator over every fixture. Fail closed: missing infra is never a pass.

Each error/fatal issue is reduced to a signature:
  min:<path>          profile/base minimum-cardinality violation (Validation_VAL_Profile_Minimum)
  invariant:<key>     FHIRPath constraint (message-id '<profile>#<key>')
  other:<msgid>@<expr> anything else
A case passes only if its set of error signatures equals manifest `expected_errors` exactly.
"""
import argparse, hashlib, json, subprocess, sys, tarfile, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXT = 'http://hl7.org/fhir/StructureDefinition/operationoutcome-'


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pinned_hashes():
    rows = (line.split() for line in (ROOT / 'deps.sha256').read_text().splitlines() if line.strip())
    return {Path(name).name: digest for digest, name in rows}


def package_metadata(path):
    with tarfile.open(path, 'r:gz') as tar:
        members = [m for m in tar.getmembers() if m.name.lstrip('./') == 'package/package.json']
        if len(members) != 1:
            raise ValueError('Expected exactly one package/package.json in FHIR NPM archive')
        return json.load(tar.extractfile(members[0]))


def ext(item, name):
    for e in item.get('extension', []):
        if e.get('url') == EXT + name:
            return e.get('valueCode') or e.get('valueString')
    return None


def outcomes(data):
    """Return {fixture path: OperationOutcome} from a validator -output file (Bundle or single OO)."""
    if data.get('resourceType') == 'Bundle':
        oos = [e.get('resource', {}) for e in data.get('entry', [])]
    elif data.get('resourceType') == 'OperationOutcome':
        oos = [data]
    else:
        raise ValueError('Validator did not produce OperationOutcome JSON')
    result = {}
    for oo in oos:
        if oo.get('resourceType') != 'OperationOutcome' or not ext(oo, 'file'):
            raise ValueError('Bundle entry is not an OperationOutcome tied to a file')
        result[ext(oo, 'file')] = oo
    return result


def signature(issue):
    msgid = ext(issue, 'message-id') or ''
    text = issue.get('details', {}).get('text', '')
    if msgid == 'Validation_VAL_Profile_Minimum' and ':' in text:
        return 'min:' + text.split(':', 1)[0]
    if '#' in msgid:
        return 'invariant:' + msgid.rsplit('#', 1)[1]
    return 'other:%s@%s' % (msgid, ','.join(issue.get('expression', [])))


def judge(case, oo):
    errors = [i for i in oo.get('issue', []) if i.get('severity') in ('error', 'fatal')]
    got = sorted({signature(i) for i in errors})
    want = sorted(set(case['expected_errors']))
    return ('PASS' if got == want else 'FAIL'), got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--jar', type=Path, default=ROOT / 'deps' / 'validator_cli.jar')
    ap.add_argument('--ig', type=Path, default=ROOT / 'deps' / 'ke.fhir.core.tgz')
    ap.add_argument('--report', type=Path, default=ROOT / 'results' / 'validation.json')
    args = ap.parse_args()
    if not args.jar.is_file() or not args.ig.is_file():
        ap.error('Missing validator JAR or IG package (run scripts/fetch_deps.sh): cannot validate')
    pins = pinned_hashes()
    for path in (args.jar, args.ig):
        if sha256(path) != pins.get(path.name):
            ap.error(f'{path} does not match deps.sha256: refusing to validate against an unpinned artifact')
    manifest = json.loads((ROOT / 'manifest.json').read_text())
    meta = package_metadata(args.ig)
    ig = manifest['ig']
    if (meta.get('name'), meta.get('version'), meta.get('canonical')) != (ig['package_id'], ig['version'], ig['canonical']):
        ap.error(f'Wrong IG package: {meta.get("name")}#{meta.get("version")} {meta.get("canonical")}')

    by_profile = {}
    for case in manifest['fixtures']:
        by_profile.setdefault(case['profile'], []).append(case)
    results, version = [], None
    with tempfile.TemporaryDirectory() as tmp:
        for n, (profile, cases) in enumerate(by_profile.items()):
            out = Path(tmp) / f'{n}.json'
            # preferIPv4Stack: validator refuses NAT64 (64:ff9b::) addresses as non-public.
            cmd = ['java', '-Djava.net.preferIPv4Stack=true', '-jar', str(args.jar), *[c['file'] for c in cases],
                   '-version', ig['fhir_version'], '-ig', str(args.ig), '-profile', profile, '-tx', 'n/a', '-output', str(out)]
            proc = None
            try:
                proc = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, timeout=600)
                parsed = outcomes(json.loads(out.read_text()))
            except (subprocess.TimeoutExpired, FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
                tail = (proc.stdout + proc.stderr)[-2000:] if proc else ''
                results += [{'id': c['id'], 'status': 'BLOCKED', 'detail': f'{type(exc).__name__}: {exc} {tail}'} for c in cases]
                print('BLOCKED', profile, exc, tail, file=sys.stderr)
                continue
            for case in cases:
                oo = parsed.get(case['file'])
                if oo is None:
                    results.append({'id': case['id'], 'status': 'BLOCKED', 'detail': 'No OperationOutcome for fixture'})
                    continue
                for e in oo.get('extension', []):
                    if e.get('url', '').endswith('validator-version'):
                        version = e.get('valueString')
                status, got = judge(case, oo)
                results.append({'id': case['id'], 'expected': case['expected'], 'status': status,
                                'expected_errors': case['expected_errors'], 'actual_errors': got, 'operation_outcome': oo})
                print(f"{case['id']:32} {status}  expected={case['expected_errors']} actual={got}")
    ok = len(results) == len(manifest['fixtures']) and all(r['status'] == 'PASS' for r in results)
    report = {'status': 'VERIFIED' if ok else 'NOT_VERIFIED', 'validator': version,
              'validator_sha256': sha256(args.jar), 'ig': f"{meta['name']}#{meta['version']} ({meta.get('date')})",
              'ig_sha256': sha256(args.ig), 'terminology': '-tx n/a (no terminology server)', 'results': results}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, indent=2) + '\n')
    print('Final:', report['status'], 'Report:', args.report)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
