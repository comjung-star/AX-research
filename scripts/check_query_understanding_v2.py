"""Run literal understanding contracts without loading any relevance scores."""
from ax_research.query_understanding_v2 import understand
from scripts.improvement_cycle import read


def check_contracts():
    cfg = read('configs/semantic_mapping_20261028.json')
    fixtures = read('configs/query_understanding_v2_contracts.json')['cases']
    rows = []
    for case in fixtures:
        p, profile = understand(case['text'], cfg)
        errors = []
        for key in ('requested', 'excluded'):
            for value in case.get(key, []):
                if value not in p[key + '_text']:
                    errors.append(key + ':' + value)
        for value in case.get('not_requested', []):
            if value in p['requested_text']:
                errors.append('forbidden_request:' + value)
        for value in case.get('actions', []):
            if value not in profile['fields']['action'].splitlines():
                errors.append('action:' + value)
        for value in case.get('not_actions', []):
            if value in profile['fields']['action'].splitlines():
                errors.append('forbidden_action:' + value)
        for value in case.get('approval', []):
            if not any(value in span['quote'] for span in p['pieces'] if span['role'] == 'human_approval'):
                errors.append('approval:' + value)
        if 'unknown' in case and p['request_unknown'] != case['unknown']:
            errors.append('unknown')
        for span in p['pieces'] + p['output_hints']:
            if case['text'][span['start']:span['end']] != span['quote']:
                errors.append('source_span')
        for spans in profile['spans'].values():
            for span in spans:
                if p['requested_text'][span['start']:span['end']] != span['quote']:
                    errors.append('field_span')
        rows.append({'id': case['id'], 'passed': not errors, 'errors': errors, 'partition': p, 'fields': profile['fields']})
    return {'passed': all(r['passed'] for r in rows), 'cases': len(rows), 'rows': rows,
            'relevance_scores_read': False, 'human_gold': False}


if __name__ == '__main__':
    report = check_contracts()
    print('PASS' if report['passed'] else 'FAIL', report['cases'], 'contracts')
    for row in report['rows']:
        if not row['passed']:
            print(row['id'], row['errors'], row['fields'], row['partition']['pieces'])
    raise SystemExit(0 if report['passed'] else 1)
