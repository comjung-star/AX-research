"""Evaluate sealed fresh mapping and report blind-review disagreements without qrels edits."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean

from scripts.autonomous_trial2_mapping_replay import interval, metrics

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/autonomous-improvement-20261108'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def evaluate(prediction, qrels):
    grades = defaultdict(dict)
    for row in qrels:
        grades[row['query_id']][row['case_id']] = row['grade']
    grouped = defaultdict(lambda: defaultdict(list))
    for row in prediction['records']:
        grouped[row['query_id']][row['policy']].append(metrics(row['ranking'], grades[row['query_id']]))
    per_query = []
    for query, policies in sorted(grouped.items()):
        per_query.append({'query_id': query, 'positive_count': sum(grade >= 2 for grade in grades[query].values()),
                          **{policy: {metric: mean(row[metric] for row in rows) if rows[0][metric] is not None else None
                                      for metric in rows[0]} for policy, rows in policies.items()}})
    summary = {}
    for metric in ('P@5', 'F1@5', 'nDCG@10'):
        eligible = [row for row in per_query if row['baseline'][metric] is not None]
        deltas = [row['proposed'][metric] - row['baseline'][metric] for row in eligible]
        summary[metric] = {'queries': len(eligible),
                           **{policy: mean(row[policy][metric] for row in eligible) for policy in ('baseline', 'proposed')},
                           'delta': mean(deltas), 'paired_bootstrap95': interval(deltas)}
    return {'summary': summary, 'per_query': per_query}


def main():
    prediction_path = OUT / '17_trial2_precision_predictions.json'
    prediction = read(prediction_path)
    qrels = read(ROOT / 'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json')['records']
    review = OUT / 'independent_review'
    plan = read(review / 'preregistration.json')
    by_provider = {}
    costs = {}
    reserved = {}
    for provider in ('anthropic', 'gemini', 'gemini31'):
        rows = [read(path) for path in sorted(review.glob(provider + '_*_validated.json'))]
        by_provider[provider] = {(row['query_id'], row['case_id']): row for batch in rows for row in batch['records']}
        costs[provider] = sum(batch['cost_usd'] for batch in rows)
        reserved[provider] = sum(read(path)['reserved_usd'] for path in review.glob(provider + '_*_receipt.json'))
    comparison = []
    for pair in sorted({tuple(pair) for pair in plan['transfer_pairs']} |
                       {(row['query_id'], row['case_id']) for batch in plan['batches'] for row in batch}):
        votes = {provider: rows.get(pair) for provider, rows in by_provider.items() if provider != 'gemini'}
        valid = [row for row in votes.values() if row and row['status'] == 'JUDGED']
        status = 'UNRESOLVED'
        if len(valid) == 2:
            signs = [row['grade'] >= 2 for row in valid]
            status = 'BOTH_POSITIVE' if all(signs) else ('BOTH_NEGATIVE' if not any(signs) else 'DISAGREEMENT')
        comparison.append({'query_id': pair[0], 'case_id': pair[1], 'status': status, 'votes': votes})
    sensitivity = {}
    for provider, votes in by_provider.items():
        if not votes:
            continue
        if any(row['grade'] is None for row in votes.values()):
            sensitivity[provider] = {'state': 'ABSTENTIONS_PREVENT_COMPLETE_SCOPE_SENSITIVITY'}
            continue
        adjusted = [{**row, 'grade': votes[row['query_id'], row['case_id']]['grade']}
                    if (row['query_id'], row['case_id']) in votes else row for row in qrels]
        sensitivity[provider] = evaluate(prediction, adjusted)
    result = {'state': 'FRESH_MATCHED20_EVALUATED', 'provisional_metrics': evaluate(prediction, qrels),
              'scoped_review_sensitivity_only': sensitivity,
              'review_counts': {provider: len(rows) for provider, rows in by_provider.items()},
              'review_comparison': comparison,
              'transfer_summary': {status: sum(row['status'] == status for row in comparison
                                               if [row['query_id'], row['case_id']] in plan['transfer_pairs'])
                                   for status in ('BOTH_POSITIVE', 'BOTH_NEGATIVE', 'DISAGREEMENT', 'UNRESOLVED')},
              'zero_queries': {query: {status: sum(row['status'] == status for row in comparison if row['query_id'] == query)
                                       for status in ('BOTH_POSITIVE', 'BOTH_NEGATIVE', 'DISAGREEMENT', 'UNRESOLVED')}
                               for query in plan['zero_queries']},
              'validated_response_cost_usd': costs, 'all_attempt_reservations_usd': reserved,
              'cost_upper_bound_usd': sum(reserved.values()), 'limit_usd': 2,
              'prediction_sha256': hashlib.sha256(prediction_path.read_bytes()).hexdigest(),
              'confirmed_performance_gain': False, 'sealed_test_opened': False,
              'limitations': ['Independent blind review covers464 selected pairs only, not all2240; remaining labels remain prior AI-Silver.',
                              'Provider disagreement/abstention is retained; original qrels never overwritten.',
                              'Posthoc candidate interleaving and provisional labels cannot establish generalization or independent model efficacy.']}
    assert result['cost_upper_bound_usd'] <= 2
    path = OUT / '18_trial2_metrics_and_independent_review.json'
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if path.exists():
        assert path.read_text(encoding='utf-8') == payload
    else:
        path.write_text(payload, encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('state', 'review_counts', 'transfer_summary', 'zero_queries', 'validated_response_cost_usd', 'cost_upper_bound_usd')}))
    print(json.dumps(result['provisional_metrics']['summary']))


if __name__ == '__main__':
    main()
