"""Evaluate candidate recall separately from unchanged DenseTop10 output quality."""
import hashlib
import json
from statistics import mean

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate, label_sets
from scripts.autonomous_trial2_mapping_replay import interval


def main():
    destination = ROOT / 'docs/dense-preserved-candidates-20261108-evaluation.json'
    if destination.exists():
        raise FileExistsError(destination)
    path = ROOT / 'docs/dense-preserved-candidates-20261108-predictions.json'
    predictions = json.loads(path.read_text(encoding='utf-8'))
    rankings = {(row['query_id'], row['repeat'], row['system']): row['ranking'] for row in predictions['rankings']}
    results = {}
    for version, grades in label_sets().items():
        result = evaluate(predictions['rankings'], grades)
        for system in ('QueryTokenCandidates', 'QuerySparseCandidates', 'PerspectiveCandidates'):
            for metric in ('F1@5', 'nDCG@10'):
                assert result['summary'][system][metric]['mean'] == result['summary']['Dense'][metric]['mean']
        candidate_rows = []
        for query in sorted(grades):
            positive = {case for case, grade in grades[query].items() if grade >= 2}
            for repeat in (1, 2, 3):
                pools = {system: set(rankings[query, repeat, system][:20]) for system in
                         ('Dense', 'QueryTokenCandidates', 'QuerySparseCandidates', 'PerspectiveCandidates')}
                candidate_rows.append({'query_id': query, 'repeat': repeat, 'positive_count': len(positive),
                    'recall': {system: len(pool & positive) / len(positive) if positive else None for system, pool in pools.items()},
                    'new_perspective_positive_vs_dense': sorted((pools['PerspectiveCandidates'] - pools['Dense']) & positive),
                    'lost_perspective_positive_vs_dense': sorted((pools['Dense'] - pools['PerspectiveCandidates']) & positive),
                    'perspective_positive_absent_both_single_controls': sorted((pools['PerspectiveCandidates'] - pools['QueryTokenCandidates'] - pools['QuerySparseCandidates']) & positive)})
        per_query = []
        for query in sorted(grades):
            rows = [row for row in candidate_rows if row['query_id'] == query]
            if rows[0]['positive_count']:
                per_query.append({'query_id': query, **{system: mean(row['recall'][system] for row in rows) for system in rows[0]['recall']}})
        comparisons = {}
        for baseline in ('Dense', 'QueryTokenCandidates', 'QuerySparseCandidates'):
            differences = [row['PerspectiveCandidates'] - row[baseline] for row in per_query]
            comparisons[baseline] = {'delta_recall20': mean(differences), 'paired_query_interval95': interval(differences)}
        counts = {'new_positive_query_case_pairs': len({(row['query_id'], case) for row in candidate_rows for case in row['new_perspective_positive_vs_dense']}),
                  'lost_positive_query_case_pairs': len({(row['query_id'], case) for row in candidate_rows for case in row['lost_perspective_positive_vs_dense']}),
                  'positive_query_case_pairs_absent_both_single_controls': len({(row['query_id'], case) for row in candidate_rows for case in row['perspective_positive_absent_both_single_controls']}),
                  'unit': 'unique query-case across repeats, not independent queries'}
        result['candidate_accounting'] = candidate_rows
        result['candidate_recall_comparisons'] = comparisons
        result['candidate_discovery_counts'] = counts
        results[version] = result
    output = {'state': 'CANDIDATE_COMPLEMENT_EVALUATED_NO_END_TO_END_GAIN_CLAIM', 'results': results,
              'paid_calls': 0, 'new40_used': False, 'labels_changed': False,
              'prediction_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'limitations': ['Previously inspected development queries', 'First10outputs identical toDense by construction',
                              'Candidate discovery is not improved final recommendation accuracy', 'No perspective-specific or strategy gold']}
    with destination.open('x', encoding='utf-8') as target:
        target.write(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    for version, result in results.items():
        print(version, {system: round(result['summary'][system]['Recall@20']['mean'], 5) for system in
                        ('Dense', 'QueryTokenCandidates', 'QuerySparseCandidates', 'PerspectiveCandidates')})
        print('differences', result['candidate_recall_comparisons'], 'discoveries', result['candidate_discovery_counts'])


if __name__ == '__main__':
    main()
