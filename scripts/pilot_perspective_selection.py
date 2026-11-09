"""Run the isolated four-card selector or its synthetic development contracts."""
import argparse
import json

from ax_research.pilot_perspective_selector import select_perspectives
from scripts.improvement_cycle import ROOT, read

CATALOG = 'docs/perspective-catalog-pilot-20261109/catalog-reviewed.json'
RULES = 'configs/pilot_perspective_selector_20261109.json'
CONTRACTS = 'configs/pilot_perspective_selector_contracts_20261109.json'


def select(question):
    return select_perspectives(question, read(CATALOG), read(RULES))


def check_contracts():
    rows = []
    for case in read(CONTRACTS)['cases']:
        result = select(case['question'])
        chosen = sorted(r['id'] for r in result['selected'])
        pending = {r['id'] for r in result['review_needed']}
        not_selected = {r['id'] for r in result['not_selected']}
        excluded = {r['id'] for r in result['not_selected'] if r['status'] == 'EXCLUDED_BY_QUERY'}
        outside = {r['id'] for r in result['outside_work']}
        errors = []
        if chosen != sorted(case['selected']):
            errors.append('selected:' + repr(chosen))
        if 'state' in case and result['state'] != case['state']:
            errors.append('state:' + result['state'])
        if case['selected'] and 'state' not in case and result['state'] != 'MATCHED':
            errors.append('unexpected_partial_or_review:' + result['state'])
        for field, actual in [('review', pending), ('not_selected', not_selected), ('excluded', excluded), ('outside', outside)]:
            if not set(case.get(field, [])) <= actual:
                errors.append(field + ':' + repr(sorted(actual)))
        if set(case.get('forbidden_outside', [])) & outside:
            errors.append('prohibited_operation_became_requested')
        for value in case.get('constraint_contains', []):
            if not any(value in e['quote'] for e in result['constraints']):
                errors.append('constraint_lost:' + value)
        evidence = list(result['clauses']) + list(result['constraints'])
        for collection in ('selected', 'review_needed', 'not_selected', 'outside_work'):
            for record in result[collection]:
                evidence.extend(record['evidence'])
        for e in evidence:
            if case['question'][e['start']:e['end']] != e['quote']:
                errors.append('nonliteral_evidence')
        if result['case_recommendations_generated']:
            errors.append('unexpected_case_recommendation')
        rows.append({'id': case['id'], 'group': case.get('group'), 'passed': not errors, 'errors': errors,
                     'expected_selected': case['selected'], 'result': result})
    groups = {}
    for row in rows:
        if row['group']:
            groups.setdefault(row['group'], []).append(sorted(r['id'] for r in row['result']['selected']))
    stable = all(all(v == values[0] for v in values) for values in groups.values())
    return {'passed': all(r['passed'] for r in rows) and stable, 'cases': len(rows), 'rows': rows,
            'paraphrase_groups': len(groups), 'paraphrase_selection_stable': stable,
            'human_gold': False, 'independent_accuracy_evaluation': False, 'paid_calls': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--question')
    parser.add_argument('--input', help='UTF-8 text file containing one question')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.check:
        report = check_contracts()
        print('PASS' if report['passed'] else 'FAIL', report['cases'], 'development contracts')
        for row in report['rows']:
            if not row['passed']:
                print(row['id'], row['errors'])
        raise SystemExit(0 if report['passed'] else 1)
    question = (ROOT / args.input).read_text(encoding='utf-8') if args.input else args.question
    if not question:
        parser.error('Use --question or --input')
    print(json.dumps(select(question), ensure_ascii=False, indent=2))
