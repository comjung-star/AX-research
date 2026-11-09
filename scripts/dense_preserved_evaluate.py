"""Compare sealed Dense preservation predictions and account for gains and losses."""
import hashlib
import json
from collections import defaultdict
from statistics import mean

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate, label_sets
from scripts.autonomous_trial2_mapping_replay import interval


def main():
    destination = ROOT / 'docs/dense-preserved-20261108-evaluation.json'
    if destination.exists():
        raise FileExistsError(destination)
    source = ROOT / 'docs/dense-preserved-20261108-predictions.json'
    predictions = json.loads(source.read_text(encoding='utf-8'))
    assert not predictions['qrels_read'] and not predictions['new40_pilot_read']
    by_key = {(row['query_id'], row['repeat'], row['system']): row['ranking'] for row in predictions['rankings']}
    results = {}
    for version, grades in label_sets().items():
        result = evaluate(predictions['rankings'], grades)
        for metric in ('F1@5', 'nDCG@10'):
            eligible = [row for row in result['per_query'].values() if row['Dense'][metric] is not None]
            differences = [row['ProtectedPerspectiveToken'][metric] - row['ProtectedToken'][metric] for row in eligible]
            result['summary']['ProtectedPerspectiveToken'][metric]['ProtectedToken'] = {'delta': mean(differences), 'interval95': interval(differences)}
        accounting = []
        for row in predictions['traces']:
            query, repeat, system = row['query_id'], row['repeat'], row['system']
            reference = set(by_key[query, repeat, 'Dense'][:5])
            selected = set(row['ranking'][:5])
            entered, departed = selected - reference, reference - selected
            candidate_positive = sum(grades[query][case] >= 2 for case in row['candidates'])
            positive_count = sum(grade >= 2 for grade in grades[query].values())
            branch_new = set(row['branch_candidates']) - set(by_key[query, repeat, 'Dense'][:20])
            accounting.append({'query_id': query, 'repeat': repeat, 'system': system,
                'positive_entered': sorted(case for case in entered if grades[query][case] >= 2),
                'positive_lost': sorted(case for case in departed if grades[query][case] >= 2),
                'negative_entered': sorted(case for case in entered if grades[query][case] < 2),
                'outside_dense20_branch_candidates': sorted(branch_new),
                'positive_outside_dense20_branch_candidates': sorted(case for case in branch_new if grades[query][case] >= 2),
                'positive_count': positive_count, 'candidate_recall': candidate_positive / positive_count if positive_count else None,
                'protected_head_matches': row['ranking'][:3] == by_key[query, repeat, 'Dense'][:3]})
        summaries = {}
        for system in ('ProtectedToken', 'ProtectedPerspectiveToken'):
            rows = [row for row in accounting if row['system'] == system]
            per_query = defaultdict(list)
            for row in rows:
                per_query[row['query_id']].append(row)
            summaries[system] = {'positive_entry_events': sum(len(row['positive_entered']) for row in rows),
                'positive_loss_events': sum(len(row['positive_lost']) for row in rows),
                'negative_entry_events': sum(len(row['negative_entered']) for row in rows),
                'query_mean_positive_entries': mean(mean(len(row['positive_entered']) for row in values) for values in per_query.values()),
                'query_mean_positive_losses': mean(mean(len(row['positive_lost']) for row in values) for values in per_query.values()),
                'branch_outside_dense20_positive_events': sum(len(row['positive_outside_dense20_branch_candidates']) for row in rows),
                'event_unit': 'query-case-repeat; not independent samples',
                'all60_protected_heads_match': all(row['protected_head_matches'] for row in rows)}
        result['accounting'] = accounting
        result['accounting_summary'] = summaries
        results[version] = result
    output = {'state': 'DENSE_PRESERVED_EXPLORATORY_DEVELOPMENT_EVALUATED', 'results': results,
              'prediction_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'paid_calls': 0,
              'new40_pilot_used_for_selection': False, 'labels_changed': False,
              'limits': ['Already inspected development data', 'Top3 protected, not all Dense positives',
                         'Extra branch compute retained; output/candidate budgets alone matched',
                         'Question labels do not establish perspective-specific gold or strategy coverage']}
    with destination.open('x', encoding='utf-8') as target:
        target.write(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    for version, result in results.items():
        for system, values in result['summary'].items():
            print(version, system, 'F1', round(values['F1@5']['mean'], 5), 'nDCG', round(values['nDCG@10']['mean'], 5), 'R20', round(values['Recall@20']['mean'], 5))
        print('accounting', version, json.dumps(result['accounting_summary']))


if __name__ == '__main__':
    main()
