#!/usr/bin/env python3
"""Run reference HL7 validator. Fail closed: never confuse missing infra with a passing result."""
import argparse, json, hashlib, subprocess, tarfile, tempfile, re, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def package_metadata(path):
    with tarfile.open(path,'r:gz') as tar:
        members=[m for m in tar.getmembers() if m.name.lstrip('./')=='package/package.json']
        if len(members)!=1: raise ValueError('Expected package/package.json in FHIR NPM archive')
        return json.load(tar.extractfile(members[0]))

def messages(data):
    if data.get('resourceType')!='OperationOutcome':
        raise ValueError('Validator did not produce an OperationOutcome JSON result')
    return [(i.get('severity',''), ' '.join([str(i.get('diagnostics','')),str(i.get('details',{}).get('text','')),' '.join(i.get('expression',[])), ' '.join(i.get('location',[]))])) for i in data.get('issue',[])]

def targeted(issue, case):
    constraint=case.get('expected_constraint','')
    path=case.get('expected_path','')
    low=issue.lower()
    if constraint!='min-cardinality' and constraint.lower() in low: return True
    if path.lower() in low and ('minimum' in low or 'min=' in low or 'required' in low or 'at least' in low or 'cannot be empty' in low):return True
    return False

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--jar',type=Path,required=True)
    ap.add_argument('--ig',type=Path,required=True,help='FHIR NPM tgz for ke.fhir.core#1.0.0')
    ap.add_argument('--report',type=Path,default=ROOT/'results'/'validation.json')
    args=ap.parse_args()
    if not args.jar.is_file() or not args.ig.is_file(): ap.error('Missing validator JAR or IG package: cannot validate')
    manifest=json.loads((ROOT/'manifest.json').read_text())
    meta=package_metadata(args.ig)
    if meta.get('name')!='ke.fhir.core' or meta.get('version')!='1.0.0':
        ap.error(f'Wrong IG package: {meta.get("name")}#{meta.get("version")}')
    args.report.parent.mkdir(parents=True,exist_ok=True)
    results=[]
    with tempfile.TemporaryDirectory() as tmp:
      for case in manifest['fixtures']:
        outfile=Path(tmp)/(case['id']+'.json')
        cmd=['java','-jar',str(args.jar),str(ROOT/case['file']),'-version','4.0.1', '-ig',str(args.ig),'-profile',case['profile'],'-tx','n/a','-output',str(outfile)]
        try:
            result=subprocess.run(cmd,capture_output=True,text=True,timeout=180)
        except subprocess.TimeoutExpired:
            results.append({'id':case['id'],'status':'BLOCKED','detail':'Validator process timed out after 180s'})
            continue
        if not outfile.exists():
            results.append({'id':case['id'],'status':'BLOCKED','detail':(result.stderr+' '+result.stdout)[-1200:]})
            continue
        try:
            issues=messages(json.loads(outfile.read_text()))
        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            results.append({'id':case['id'],'status':'BLOCKED','detail':str(exc)})
            continue
        errors=[detail for severity,detail in issues if severity in ('error','fatal')]
        if result.returncode != 0 and not errors:
            results.append({'id':case['id'],'status':'BLOCKED','detail':'Validator exited nonzero without an error issue: '+(result.stdout+' '+result.stderr)[-1200:]})
            continue
        if case['expected']=='pass':
            status='PASS' if not errors else 'FAIL'
        else:
            intended=[e for e in errors if targeted(e,case)]
            unexpected=[e for e in errors if not targeted(e,case)]
            status='PASS' if intended and not unexpected else 'FAIL'
        results.append({'id':case['id'],'status':status,'errors':errors,'all_issues':issues})
        print(case['id'],status,':',len(errors),'error(s)')
    output={'status':'VERIFIED' if all(r['status']=='PASS' for r in results) else 'NOT_VERIFIED','ig_sha256':hashlib.sha256(args.ig.read_bytes()).hexdigest(),'validator_sha256':hashlib.sha256(args.jar.read_bytes()).hexdigest(),'results':results}
    args.report.write_text(json.dumps(output,indent=2)+'\n')
    print('Final:',output['status'],'Report:',args.report)
    return 0 if output['status']=='VERIFIED' else 1

if __name__=='__main__':sys.exit(main())
