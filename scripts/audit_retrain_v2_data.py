"""Audit existing labels and candidate coverage, without relabeling or new fitting."""
from itertools import combinations
from statistics import mean

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import label_sets
from scripts.ai_pilot_evaluate import assemble_votes
from scripts.retrain_v2_20261109 import OUT, write
from scripts.task_alignment_20261109 import sha


def describe(grades, inputs):
    counts = {q: sum(v >= 2 for v in row.values()) for q, row in grades.items()}
    positive_cases = {c for row in grades.values() for c, v in row.items() if v >= 2}
    coverage = []
    for q, positive in counts.items():
        if not positive:
            continue
        row = {'query_id': q, 'positives': positive}
        for pool in ('DensePool', 'PerspectivePool'):
            hits = [sum(grades[q][c] >= 2 for c in inputs[q]['pools'][str(r)][pool]) for r in (1, 2, 3)]
            row[pool] = {'mean_positive_candidates': mean(hits), 'recall20': mean(hits) / positive,
                         'oracle_f1_upper_bound': mean(2 * min(5, v) / (5 + positive) for v in hits)}
        coverage.append(row)
    return {'queries': len(grades), 'pairs': sum(len(row) for row in grades.values()),
            'positive_pairs': sum(counts.values()), 'positive_queries': sum(v > 0 for v in counts.values()),
            'zero_positive_queries': [q for q, v in counts.items() if not v],
            'one_positive_queries': [q for q, v in counts.items() if v == 1],
            'positive_counts_by_query': counts, 'case_ids_ever_positive': len(positive_cases),
            'candidate_coverage_by_positive_query': coverage,
            'positive_queries_with_no_dense_candidate_positive': [r['query_id'] for r in coverage if r['DensePool']['mean_positive_candidates'] == 0],
            'mean_oracle_f1_upper_bound': {p: mean(r[p]['oracle_f1_upper_bound'] for r in coverage) for p in ('DensePool', 'PerspectivePool')},
            'oracle_is_label_aware_diagnostic_not_achieved_performance': True}


def main():
    labels20 = label_sets()
    votes, consensus = assemble_votes()
    labels40 = {}
    for provider, records in votes.items():
        grades = {}
        for (q, c), row in records.items():
            assert row['status'] == 'JUDGED' and row['grade'] is not None
            grades.setdefault(q, {})[c] = row['grade']
        labels40[provider] = grades
    inputs20 = read('docs/query-understanding-v2-20261109/dev20-inputs.json')['inputs']
    inputs40 = read('docs/query-understanding-v2-20261109/reuse40-inputs.json')['inputs']
    comparisons = {}
    for first, second in combinations(labels20, 2):
        a, b = labels20[first], labels20[second]
        keys = [(q, c) for q, row in a.items() for c in row]
        comparisons[first + ':' + second] = {'binary_disagreements': sum((a[q][c] >= 2) != (b[q][c] >= 2) for q, c in keys),
                                            'grade_disagreements': sum(a[q][c] != b[q][c] for q, c in keys),
                                            'pairs': len(keys)}
    a, b = labels40['claude'], labels40['gemini']
    matrix = {'both_positive': 0, 'claude_only_positive': 0, 'gemini_only_positive': 0, 'both_negative': 0}
    for q, values in a.items():
        for c, grade in values.items():
            pa, pb = grade >= 2, b[q][c] >= 2
            key = 'both_positive' if pa and pb else 'claude_only_positive' if pa else 'gemini_only_positive' if pb else 'both_negative'
            matrix[key] += 1
    union = matrix['both_positive'] + matrix['claude_only_positive'] + matrix['gemini_only_positive']
    cases = read('docs/literal-action-recovery-20261109/case_profiles.json')
    write('data-audit.json', {'state': 'EXISTING_DATA_AUDIT_NO_RELABELING',
        'dev20': {v: describe(g, inputs20) for v, g in labels20.items()},
        'reuse40': {v: describe(g, inputs40) for v, g in labels40.items()},
        'dev_label_version_differences': comparisons, 'reuse40_binary_matrix': matrix,
        'reuse40_positive_jaccard': matrix['both_positive'] / union,
        'reuse40_overall_binary_agreement': (matrix['both_positive'] + matrix['both_negative']) / sum(matrix.values()),
        'case_field_presence': {f: sum(bool(row['fields'][f]) for row in cases.values()) for f in ('task', 'action', 'object', 'output', 'context')},
        'query_structure': {'old84x30': '10 original questions x3 reference perspectives x84 cases; not30 independent questions',
                            'dev20x112': '20 original questions; versions are sensitivity labels, not independent datasets',
                            'reuse40x112': '40 AI-authored previously observed queries; not final test'},
        'interpretation': ['A zero-positive query may indicate strict judgments or corpus gap; this audit cannot distinguish them',
                           'Large pair count does not provide equally many independent questions',
                           'High negative agreement does not establish positive relevance validity',
                           '464-pair review is partial; neither version is human Gold',
                           'Direct task match and cross-domain functional transfer are not interchangeable evaluation claims'],
        'actions_not_taken': ['No new questions/cases/grades generated', 'No adjudication or human Gold claim',
                              'No tests opened, no new API, no additional model search'],
        'paid_calls': 0, 'new_labels': 0})
    print('DATA_AUDIT', matrix, 'positive_jaccard', round(matrix['both_positive'] / union, 5))
    print('DEV20_POSITIVES', {v: sum(g >= 2 for row in grades.values() for g in row.values()) for v, grades in labels20.items()})


if __name__ == '__main__':
    main()
