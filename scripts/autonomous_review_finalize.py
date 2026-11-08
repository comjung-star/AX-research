"""Preserve original qrels and publish scoped three-model AI-Silver adjudication."""
import json

from scripts.autonomous_blind_review import OUT, read
from scripts.autonomous_trial2_evaluate import evaluate


def main():
    first = read(OUT.parent / '18_trial2_metrics_and_independent_review.json')
    third = { (row['query_id'], row['case_id']): row
             for path in OUT.glob('sonnet_fixed_*_validated.json') for row in read(path)['records']}
    rows = []
    for entry in first['review_comparison']:
        entry = {**entry, 'third_vote': third.get((entry['query_id'], entry['case_id']))}
        votes = [vote for vote in list(entry['votes'].values()) + [entry['third_vote']]
                 if vote is not None and vote['status'] == 'JUDGED']
        positive = sum(vote['grade'] >= 2 for vote in votes)
        negative = len(votes) - positive
        agreed = positive >= 2 or negative >= 2
        entry['adjudication'] = 'POSITIVE' if positive >= 2 else ('NEGATIVE' if negative >= 2 else 'UNRESOLVED')
        agreeing = [vote['grade'] for vote in votes if (vote['grade'] >= 2) == (positive >= 2)]
        entry['conservative_grade'] = min(agreeing) if agreed else None
        rows.append(entry)
    plan = read(OUT / 'preregistration.json')
    transfers = [row for row in rows if [row['query_id'], row['case_id']] in plan['transfer_pairs']]
    consensus = {(row['query_id'], row['case_id']): row['conservative_grade'] for row in rows}
    from scripts.autonomous_trial2_evaluate import ROOT
    original = read(ROOT / 'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json')['records']
    sensitivity = None
    if all(grade is not None for grade in consensus.values()):
        adjusted = [{**row, 'grade': consensus.get((row['query_id'], row['case_id']), row['grade'])} for row in original]
        sensitivity = evaluate(read(OUT.parent / '17_trial2_precision_predictions.json'), adjusted)
    costs = sum(read(path)['cost_usd'] for path in OUT.glob('*_validated.json'))
    upper = sum(read(path)['reserved_usd'] for path in OUT.glob('*_receipt.json'))
    assert upper <= 2
    result = {'state': 'SCOPED_INDEPENDENT_AI_REVIEW_COMPLETE', 'rows': rows,
              'third_model_pairs': len(third), 'model_count': 3 if third else 2, 'provider_count': 2,
              'transfer_summary': {status: sum(row['adjudication'] == status for row in transfers)
                                   for status in ('POSITIVE', 'NEGATIVE', 'UNRESOLVED')},
              'zero_query_summary': {query: {status: sum(row['adjudication'] == status for row in rows if row['query_id'] == query)
                                              for status in ('POSITIVE', 'NEGATIVE', 'UNRESOLVED')}
                                     for query in plan['zero_queries']},
              'scoped_consensus_sensitivity': sensitivity,
              'cost_known_usage_usd': costs, 'cost_all_attempts_upper_usd': upper,
              'original_labels_changed': False, 'human_gold': False,
              'confirmed_performance_gain': False,
              'decision': 'Close Trial2 as exploratory non-confirmatory result; do not spend Trials3to5 tuning to unstable labels.',
              'limitations': ['Independent consensus covers464 of2240 pairs; other1776 retain original AI-Silver labels.',
                              'Third model is independent blind context, same provider as first; not three independent providers.',
                              'Majority AI agreement is not externally certified ground truth; human review remains needed for paper-level gold claims.']}
    target = OUT.parent / '19_independent_adjudication_and_stop_decision.json'
    payload = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    if target.exists():
        assert target.read_text(encoding='utf-8') == payload
    else:
        target.write_text(payload, encoding='utf-8')
    print(json.dumps({key: result[key] for key in ('state', 'third_model_pairs', 'transfer_summary', 'zero_query_summary', 'cost_known_usage_usd', 'cost_all_attempts_upper_usd')}))
    if sensitivity:
        print(json.dumps(sensitivity['summary']))


if __name__ == '__main__':
    main()
