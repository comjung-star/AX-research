"""Fixed-policy evaluation on the frozen new-Dev AI-Silver dataset."""
from collections import Counter, defaultdict
from itertools import combinations
from statistics import mean, pstdev

import numpy as np
from ax_research.heldout import jsonl, read, sha, write
from scripts import fixed_three_evaluate as existing
from scripts import core_preservation_run as run
from scripts.core_preservation_quality import FIELDS


def evaluate(prediction, labels):
    translated = {**prediction, 'systems': {**prediction['systems'],
                                           'D': prediction['systems']['E']}}
    translated['systems'].pop('E')
    rows = existing.evaluate_conditions(translated, labels)
    macro = existing.summarize(rows)
    leave_one = {q: existing.summarize(rows, [q]) for q in prediction['query_ids']}
    for row in rows+macro+[r for group in leave_one.values() for r in group]:
        if row['condition'] == 'D':
            row['condition'] = 'E'
    return rows, macro, leave_one


def quality_summary():
    data = read(run.OUT/'quality.json')
    mapping = {(r['query_id'], r['id']): r for r in data['mapping']}
    assessments = [{**r, 'condition': mapping[r['query_id'], r['id']]['condition'],
                    'repeat': mapping[r['query_id'], r['id']]['repeat']}
                   for r in data['assessments']]
    summary = []
    for condition in ('B', 'C', 'E'):
        subset = [r for r in assessments if r['condition'] == condition]
        summary.append({'condition': condition, 'n': len(subset),
                        'mean_scores0to2': {field: mean(r[field] for r in subset) for field in FIELDS},
                        'fully_preserved_count': {field: sum(r[field] == 2 for r in subset) for field in FIELDS},
                        'unsupported_candidate_count': sum(bool(r['unsupported_quotes']) for r in subset),
                        'unsupported_claim_quote_count': sum(len(r['unsupported_quotes']) for r in subset)})
    literal = []
    for repeat in (1, 2, 3):
        for question in jsonl(run.QUESTIONS):
            core = read(run.OUT/'api/results'/f"X_{question['query_id']}_r{repeat}.json")['data']['core']
            for name, value in core.items():
                value = value or {'text': None, 'evidence': []}
                literal.append({'query_id': question['query_id'], 'repeat': repeat, 'field': name,
                                'unknown': value['text'] is None,
                                'has_evidence': bool(value['evidence']),
                                'all_quotes_literal': all(e in question['text'] for e in value['evidence'])})
    questions = {q['query_id']: q['text'] for q in jsonl(run.QUESTIONS)}
    quote_checks = [
        {'condition': s['condition'], 'query_id': s['query_id'], 'repeat': s['repeat'],
         'view': s['id'], 'source_quote_literal': bool(s['source_quote']) and
         s['source_quote'] in questions[s['query_id']]}
        for s in read(run.OUT/'slots.json')['records'] if s.get('status') != 'MISSING']
    return {'assessments': assessments, 'summary': summary, 'extraction_evidence_checks': literal,
            'view_source_quote_checks': quote_checks,
            'same_model_not_human_gold': True,
            'literal_quotes_do_not_prove_semantic_correctness': True}


def diagnostics(pred, labels):
    label = {(r['query_id'], r['case_id']): r for r in labels}
    positive = defaultdict(set)
    for r in labels:
        if r['grade'] is not None and r['grade'] >= 2:
            positive[r['query_id']].add(r['case_id'])
    rankings = {(c, r['query_id'], r.get('repeat', 0)): r['ranking']
                for c, rows in pred['systems'].items() for r in rows}
    changes = []
    for baseline in 'ABC':
        for q in pred['query_ids']:
            for repeat in (1, 2, 3):
                a = rankings[baseline, q, 0 if baseline == 'A' else repeat]
                b = rankings['E', q, repeat]
                for k in (5, 10, 20):
                    old = set(a[:k]) & positive[q]
                    new = set(b[:k]) & positive[q]
                    changes.append({'baseline': baseline, 'query_id': q, 'repeat': repeat, 'k': k,
                                    'gained': sorted(new-old), 'lost': sorted(old-new),
                                    'retained': sorted(old & new),
                                    'unknown_old': sum(label[q, c]['grade'] is None for c in a[:k]),
                                    'unknown_new': sum(label[q, c]['grade'] is None for c in b[:k])})
    profiles = read(run.OUT/'inference/query_profiles.json')['C1_rule']
    branches = {r['query_id']: r['ranking'] for r in read(
        run.OUT/'inference/branch_rankings.json')['systems']['C1']}
    slots = read(run.OUT/'slots.json')['records']
    reference = read(run.OUT/'function_reference.json')['questions']
    recognition = []
    for condition in ('B', 'C', 'E'):
        for q in pred['query_ids']:
            for repeat in (1, 2, 3):
                ids = [s['path_id'] for s in slots if
                       (s['condition'], s['query_id'], s['repeat']) == (condition, q, repeat)
                       and s['path_id'] in profiles]
                found = set().union(*(set(profiles[path]['function_ids']) for path in ids))
                expected = set(reference[q]['required'])
                allowed = expected | set(reference[q].get('allowed_auxiliary', []))
                recognition.append({
                    'condition': condition, 'query_id': q, 'repeat': repeat,
                    'any_recognized': bool(found), 'recognized_ids': sorted(found),
                    'required_ids': sorted(expected), 'representable': bool(expected),
                    'all_required_found': expected <= found if expected else None,
                    'off_core_ids_for_review': sorted(found-allowed),
                })
    paths = []
    for s in slots:
        path = s['path_id']
        if path not in branches:
            continue
        peers = [p['path_id'] for p in slots
                 if (p['condition'], p['query_id'], p['repeat']) ==
                 (s['condition'], s['query_id'], s['repeat'])
                 and p['path_id'] != path and p['path_id'] in branches]
        for k in (5, 10, 20):
            found = set(branches[path][:k]) & positive[s['query_id']]
            others = set().union(*(set(branches[p][:k]) for p in peers))
            paths.append({'condition': s['condition'], 'query_id': s['query_id'],
                          'repeat': s['repeat'], 'view': s['id'], 'path_id': path, 'k': k,
                          'related_cases': sorted(found), 'unique_cases': sorted(found-others),
                          'functions': profiles[path]['function_ids']})
    # Correct function links are measured on relevance-positive pairs. Function
    # existence alone is kept as a different, weaker diagnostic.
    mappings = []
    for r in jsonl(run.OUT/'inference/branch_scores.jsonl'):
        if label[r['path_id'].split('_')[1], r['case_id']]['grade'] is not None:
            q = r['path_id'].split('_')[1]
            if label[q, r['case_id']]['grade'] >= 2:
                mappings.append({'path_id': r['path_id'], 'query_id': q, 'case_id': r['case_id'],
                                 'grade': label[q, r['case_id']]['grade'],
                                 'shared_functions': r['C1_rule']['shared_functions'],
                                 'rule_strength': r['C1_rule']['mapping_grade'],
                                 'semantic': r['semantic']['score']})
    stability = []
    for condition in ('B', 'C', 'E'):
        for q in pred['query_ids']:
            for a, b in combinations((1, 2, 3), 2):
                for k in (5, 10, 20):
                    left, right = (set(rankings[condition, q, r][:k]) for r in (a, b))
                    stability.append({'condition': condition, 'query_id': q, 'k': k,
                                      'repeats': [a, b], 'topk_jaccard': len(left & right)/len(left | right)})
    return {'changes': changes, 'path_discovery': paths, 'ranking_stability': stability,
            'source_referenced_function_recognition': recognition,
            'positive_pair_function_links': mappings,
            'interpretation': 'A shared rule on an AI-positive pair is still a proxy, not verified semantic alignment'}


def bootstrap(rows, macro):
    lookup = {(r['condition'], r['query_id'], r['repeat']): r for r in rows}
    groups = {(r['condition'], r['metric']): r for r in macro}
    rng = np.random.default_rng(20261107)
    results = []
    for baseline in 'ABC':
        for metric in ('F1@5', 'F1@10', 'F1@20', 'nDCG@5', 'nDCG@10'):
            queries = groups['E', metric]['questions']
            differences = []
            for q in queries:
                e = mean(lookup['E', q, r]['metrics'][metric] for r in (1, 2, 3))
                repeats = (0,) if baseline == 'A' else (1, 2, 3)
                b = mean(lookup[baseline, q, r]['metrics'][metric] for r in repeats)
                differences.append(e-b)
            if differences:
                samples = rng.choice(differences, size=(10000, len(differences)), replace=True).mean(axis=1)
                interval = np.quantile(samples, [.025, .975]).tolist()
                value = mean(differences)
            else:
                interval, value = [None, None], None
            results.append({'baseline': baseline, 'metric': metric, 'questions': queries,
                            'mean_E_minus_baseline': value, 'paired_question_bootstrap95': interval,
                            'replicate_count': 10000, 'seed': 20261107})
    return results


def incomplete_f1_bounds(prediction, labels):
    """Exact binary-label difference bounds, without filling missing labels.

    For a fixed unknown-positive count, the common F1 denominator is fixed.
    Selecting the smallest/largest membership coefficients gives its extrema.
    This also averages the three generation runs before comparing questions.
    """
    by_query = {q: {r['case_id']: r['grade'] for r in labels if r['query_id'] == q}
                for q in prediction['query_ids']}
    results = []
    for baseline in 'ABC':
        for k in (5, 10, 20):
            per_query = []
            for q, grades in by_query.items():
                positives = {c for c, g in grades.items() if g is not None and g >= 2}
                unknown = [c for c, g in grades.items() if g is None]
                if not positives:
                    per_query.append({'query_id': q, 'lower': None, 'upper': None,
                                      'reason': 'ZERO_POSITIVE_POSSIBILITY'})
                    continue
                def membership(condition):
                    ranks = [set(r['ranking'][:k]) for r in prediction['systems'][condition]
                             if r['query_id'] == q]
                    return {c: sum(c in rank for rank in ranks)/len(ranks)
                            for c in grades}
                left, right = membership('E'), membership(baseline)
                fixed = sum(left[c]-right[c] for c in positives)
                weights = sorted(left[c]-right[c] for c in unknown)
                low = [2*(fixed+sum(weights[:m]))/(k+len(positives)+m)
                       for m in range(len(weights)+1)]
                high = [2*(fixed+sum(weights[len(weights)-m:]))/(k+len(positives)+m)
                        for m in range(len(weights)+1)]
                per_query.append({'query_id': q, 'lower': min(low), 'upper': max(high),
                                  'unknown': len(unknown)})
            complete = all(r['lower'] is not None for r in per_query)
            results.append({'baseline': baseline, 'metric': f'F1@{k}',
                            'n': len(per_query), 'per_query': per_query,
                            'lower': mean(r['lower'] for r in per_query) if complete else None,
                            'upper': mean(r['upper'] for r in per_query) if complete else None,
                            'interpretation': 'identification bounds, not imputed metrics or confidence intervals'})
    return results


def main():
    seal = read(run.OUT/'prediction_seal.json')
    for name, digest in seal['files'].items():
        assert sha(run.OUT/name) == digest
    prediction = read(run.OUT/'predictions.json')
    labels = read(run.OUT/'labels.json')['records']
    assert len(labels) == 896 and len({(r['query_id'], r['case_id']) for r in labels}) == 896
    rows, macro, leave_one = evaluate(prediction, labels)
    write(run.OUT/'evaluation.json', {'per_query': rows, 'macro': macro, 'leave_one_out': leave_one,
                                      'bootstrap': bootstrap(rows, macro),
                                      'incomplete_f1_difference_bounds': incomplete_f1_bounds(prediction, labels),
                                      'label_source': 'new Dev single-model AI-Silver',
                                      'label_counts': dict(Counter(r['status'] for r in labels))})
    write(run.OUT/'quality_summary.json', quality_summary())
    write(run.OUT/'discovery.json', diagnostics(prediction, labels))
    write(run.OUT/'evaluation_seal.json', {'files': {
        name: sha(run.OUT/name) for name in ('evaluation.json', 'quality_summary.json',
                                             'discovery.json', 'labels.json', 'quality.json')},
        'prediction_seal_sha256': sha(run.OUT/'prediction_seal.json'),
        'parameters_tuned': False})


if __name__ == '__main__':
    main()
