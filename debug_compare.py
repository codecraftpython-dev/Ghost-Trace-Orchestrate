import csv, importlib.util, json
from pathlib import Path
root = Path(r'D:\Professional work\GIT\hackerrank-orchestrate-october26-main\hackerrank-orchestrate-october26-main')
spec = importlib.util.spec_from_file_location('mainmod', root / 'code' / 'main.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
sample_rows = list(csv.DictReader(open(root / 'dataset' / 'sample_deletion_requests.csv', newline='', encoding='utf-8')))
identities = list(csv.DictReader(open(root / 'dataset' / 'user_identities.csv', newline='', encoding='utf-8')))
expected = {r['case_id']: r for r in csv.DictReader(open(root / 'dataset' / 'sample_output.csv', newline='', encoding='utf-8'))}
identity_idx = {r['email'].strip().lower(): r for r in identities}
out=[]
for case in sample_rows:
    identity = identity_idx.get((case.get('email') or '').strip().lower()) or {'email': case.get('email',''), 'user_id':'', 'phone':'', 'email_hash':''}
    status, steps = mod.build_case(case, identity, mod.read_evidence_index())
    out.append({'case_id': case['case_id'], 'deletion_status': status, 'steps_json': json.dumps(steps, separators=(',', ':'), ensure_ascii=False)})
for row in out:
    exp = expected.get(row['case_id'])
    if not exp or row['deletion_status'] != exp['deletion_status'] or row['steps_json'] != exp['steps_json']:
        if exp:
            print('Mismatch for', row['case_id'])
            print('got', row)
            print('exp', exp)
        else:
            print('missing', row['case_id'])
