import csv
import importlib.util
import json
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from backend.main import app

ROOT = Path(__file__).resolve().parents[2]


def load_code_main():
    spec = importlib.util.spec_from_file_location('code_main', ROOT / 'code' / 'main.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

ROOT = Path(__file__).resolve().parents[2]


class GhostTraceAPITest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        response = self.client.get('/api/health')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['status'], 'ok')

    def test_summary(self):
        response = self.client.get('/api/summary')
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn('total_requests', payload)
        self.assertGreaterEqual(payload['total_requests'], 1)

    def test_cases_list(self):
        response = self.client.get('/api/cases?page=1&page_size=10')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('items', data)
        self.assertGreaterEqual(len(data['items']), 1)

    def test_export_output(self):
        response = self.client.get('/api/export/output.csv')
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/csv', response.headers.get('content-type', ''))

    def test_validation_contract(self):
        with open(ROOT / 'output.csv', newline='', encoding='utf-8') as fh:
            rows = list(csv.DictReader(fh))
        self.assertEqual(len(rows), 518)
        sorted_rows = sorted(rows, key=lambda r: int(r['case_id'].split('_')[-1]))
        self.assertEqual([r['case_id'] for r in rows], [r['case_id'] for r in sorted_rows])
        for row in rows:
            self.assertIn(row['deletion_status'], {'COMPLETE', 'INCOMPLETE', 'NOT_APPLICABLE'})
            json.loads(row['steps_json'])

    def test_sample_outputs_match_expected(self):
        mod = load_code_main()
        sample_rows = list(csv.DictReader(open(ROOT / 'dataset' / 'sample_deletion_requests.csv', newline='', encoding='utf-8')))
        identities = list(csv.DictReader(open(ROOT / 'dataset' / 'user_identities.csv', newline='', encoding='utf-8')))
        expected = {row['case_id']: row for row in csv.DictReader(open(ROOT / 'dataset' / 'sample_output.csv', newline='', encoding='utf-8'))}
        alias_index = {r['email'].strip().lower(): r for r in identities}

        for case in sample_rows:
            identity = alias_index.get((case.get('email') or '').strip().lower()) or {
                'email': case.get('email', ''),
                'user_id': '',
                'phone': '',
                'email_hash': '',
            }
            status, steps = mod.build_case(case, identity, mod.read_evidence_index())
            actual = {
                'case_id': case['case_id'],
                'deletion_status': status,
                'steps_json': json.dumps(steps, separators=(',', ':'), ensure_ascii=False),
            }
            self.assertEqual(actual, expected[case['case_id']])

    def test_historical_email_resolution(self):
        mod = load_code_main()
        users = list(csv.DictReader(open(ROOT / 'dataset' / 'user_identities.csv', newline='', encoding='utf-8')))
        audit_log = list(csv.DictReader(open(ROOT / 'dataset' / 'user_audit_log.csv', newline='', encoding='utf-8')))
        case = {'email': 'noah.f438085@outlook.com'}
        identity = mod.resolve_case_identity(case, users, audit_log)
        self.assertEqual(identity['user_id'], 'user_29')
        self.assertIn('noah.f4380@outlook.com', identity['historical_emails'])
        self.assertIn('noah.f438085@outlook.com', identity['historical_emails'])


if __name__ == '__main__':
    unittest.main()
