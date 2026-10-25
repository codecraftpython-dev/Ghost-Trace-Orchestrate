import csv, json, importlib.util
from pathlib import Path
root = Path(r'D:\Professional work\GIT\hackerrank-orchestrate-october26-main\hackerrank-orchestrate-october26-main')
spec = importlib.util.spec_from_file_location('mainmod', root / 'code' / 'main.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
rows = list(csv.DictReader(open(root/'dataset'/'sample_deletion_requests.csv', newline='', encoding='utf-8')))
ident = list(csv.DictReader(open(root/'dataset'/'user_identities.csv', newline='', encoding='utf-8')))
idx = {r['email'].strip().lower(): r for r in ident}
for cid in ['case_01','case_02','case_31','case_32']:
    case = next(r for r in rows if r['case_id']==cid)
    identity = idx.get((case.get('email') or '').strip().lower()) or {'email': case.get('email',''), 'user_id':'', 'phone':'', 'email_hash':''}
    print('CASE', cid, case['request_text'])
    print('requested?', any(w in (case.get('request_text') or '').lower() for w in ('delet','eras','remove','close my account','close this account','personal-data','right to be forgotten','exclus','eliminaci','suppression','??','??','??')))
    recs = mod.evidence_records(identity, case.get('audit_at'), mod.read_evidence_index())
    print('nrecs', len(recs))
    for r in recs[:5]:
        print(' ', r['evidence_id'], r['system_id'], r['resource_id'], r['category'], r['state'])
    status, steps = mod.build_case(case, identity, mod.read_evidence_index())
    print('status', status, 'steps', steps)
    print('---')
