import csv, json, importlib.util
from pathlib import Path
root = Path(r'D:\Professional work\GIT\hackerrank-orchestrate-october26-main\hackerrank-orchestrate-october26-main')
spec = importlib.util.spec_from_file_location('mainmod', root / 'code' / 'main.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
identities = list(csv.DictReader(open(root / 'dataset' / 'user_identities.csv', newline='', encoding='utf-8')))
idx = {r['email'].strip().lower(): r for r in identities}
for email in ['amina.elmasri@gmail.com','mateo.rios@outlook.com','a.eze08@gmail.com','addo.kofi@gmail.com']:
    identity = idx.get(email.lower())
    print('EMAIL', email, 'IDENTITY', identity)
    case = {'email': email, 'audit_at': '2026-09-15T12:00:00Z', 'request_text': 'close account'}
    recs = mod.evidence_records(identity, case['audit_at'], mod.read_evidence_index())
    print('recs count', len(recs))
    for r in recs[:10]:
        print(' ', r['evidence_id'], r['system_id'], r['resource_id'], r['category'], r['state'], r['observed_at'])
    status, steps = mod.build_case(case, identity, mod.read_evidence_index())
    print('status', status, 'steps', steps[:5])
    print()
