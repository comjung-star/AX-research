"""Evaluate frozen Dev predictions and preserve per-query and per-path evidence."""
from collections import defaultdict
from statistics import mean, pstdev

from ax_research.heldout import jsonl, read, sha, write
from ax_research.new_validation import evaluate
from scripts.fixed_three_views import DEV, LABELS, OUT, PRIOR, ROOT

CONDITIONS = 'ABCD'
K = (5, 10, 20)


def summarize(rows, excluded=()):
    lookup = {(r['condition'], r['query_id'], r['repeat']): r for r in rows}
    complete = sorted({r['query_id'] for r in rows if r['complete112']} - set(excluded))
    result = []
    for metric in rows[0]['metrics']:
        eligible = [
            q for q in complete
            if all(lookup[c, q, r]['metrics'][metric] is not None
                   for c in CONDITIONS for r in ((0,) if c == 'A' else (1, 2, 3)))
        ]
        for condition in CONDITIONS:
            repetitions = (0,) if condition == 'A' else (1, 2, 3)
            values = [mean(lookup[condition, q, r]['metrics'][metric] for q in eligible)
                      for r in repetitions] if eligible else []
            result.append({'condition': condition, 'metric': metric, 'questions': eligible,
                           'n': len(eligible), 'mean': mean(values) if values else None,
                           'repeat_values': values, 'repeat_sd': pstdev(values) if len(values) > 1 else None})
    return result


def evaluate_conditions(predictions, labels):
    rows = []
    for repeat in (1, 2, 3):
        # Existing evaluator has three slots. Original is evaluated in a separate
        # pass and the three view conditions share the same evaluator call.
        mapping = {'C0': 'B', 'C1': 'C', 'C1_NO_EMBEDDING': 'D'}
        systems = {slot: [r for r in predictions['systems'][name] if r['repeat'] == repeat]
                   for slot, name in mapping.items()}
        result = evaluate({**predictions, 'systems': systems}, labels)
        rows.extend({**row, 'condition': mapping[row['system']], 'repeat': repeat}
                    for row in result['per_query'])
    original = {slot: predictions['systems']['A'] for slot in mapping}
    rows.extend({**row, 'condition': 'A', 'repeat': 0}
                for row in evaluate({**predictions, 'systems': original}, labels)['per_query']
                if row['system'] == 'C1')
    return rows


def diagnostics(predictions, labels, slots, output):
    positives = defaultdict(set)
    for row in labels:
        if row['status'] == 'JUDGED' and row['grade'] >= 2:
            positives[row['query_id']].add(row['case_id'])
    rank = {(c, r['query_id'], r.get('repeat', 0)): r['ranking']
            for c, rs in predictions['systems'].items() for r in rs}
    changes = []
    for left, right in ('AB', 'AC', 'BC', 'DC'):
        for query in predictions['query_ids']:
            for repeat in (1, 2, 3):
                for k in K:
                    a = set(rank[left, query, 0 if left == 'A' else repeat][:k]) & positives[query]
                    b = set(rank[right, query, repeat][:k]) & positives[query]
                    changes.append({'from': left, 'to': right, 'query_id': query, 'repeat': repeat,
                                    'k': k, 'gained': sorted(b-a), 'lost': sorted(a-b),
                                    'retained': sorted(a & b)})
    profiles = read(output / 'inference/query_profiles.json')['C1_rule']
    branches = {r['query_id']: r['ranking']
                for r in read(output / 'inference/branch_rankings.json')['systems']['C1']}
    if output.resolve() != OUT.resolve():
        profiles.update(read(OUT/'inference/query_profiles.json')['C1_rule'])
        branches.update({r['query_id']: r['ranking']
                         for r in read(OUT/'inference/branch_rankings.json')['systems']['C1']
                         if r['query_id'].startswith('dynamic_')})
    paths = []
    for slot in slots:
        if slot['path_id'] not in branches:
            continue
        path = slot['path_id']
        q = slot['query_id']
        peers = [s['path_id'] for s in slots if (s['query_id'], s['repeat'], s['kind']) ==
                 (q, slot['repeat'], slot['kind']) and s['path_id'] != path and s['path_id'] in branches]
        for k in K:
            hits = set(branches[path][:k]) & positives[q]
            other_hits = set().union(*(set(branches[p][:k]) for p in peers))
            paths.append({'kind': slot['kind'], 'view': slot['id'], 'path_id': path, 'query_id': q,
                          'repeat': slot['repeat'], 'k': k, 'known_relevant': sorted(hits),
                          'unique_within_triplet': sorted(hits-other_hits),
                          'new_vs_A': sorted(hits-set(rank['A', q, 0][:k])),
                          'functions': profiles[path]['function_ids']})
    return changes, paths


def main(output=OUT):
    plan = read(OUT / 'preregistration.json')
    assert sha(LABELS) == plan['files'][LABELS.relative_to(ROOT).as_posix()]
    path, seal = ('predictions.json', 'prediction_seal.json') if output.resolve() == OUT.resolve() else (
        'comparison_predictions.json', 'comparison_seal.json')
    assert sha(output / path) == read(output / seal)['predictions_sha256']
    predictions = read(output / path)
    assert predictions['systems']['A'] == read(DEV / 'predictions/rankings.json')['systems']['C1']
    labels = read(LABELS)['records']
    slots = read(output / 'slots.json')['records']
    rows = evaluate_conditions(predictions, labels)
    changes, paths = diagnostics(predictions, labels, slots, output)
    write(output / 'evaluation.json', {
        'label_source': 'frozen v2 AI-Silver', 'per_query': rows, 'macro': summarize(rows),
        'three_searchable_paths_sensitivity': summarize(
            rows, {s['query_id'] for s in slots if s.get('status') == 'MISSING'}),
        'leave_one_out': {q: summarize(rows, [q]) for q in predictions['query_ids']},
        'changes': changes, 'path_discovery': paths,
        'historical_reference': {
            'file': str((PRIOR / 'stage3/evaluation/summary.json').relative_to(ROOT)),
            'comparable': False, 'reason': 'Historical dynamic perspective count was variable',
        },
    })


if __name__ == '__main__':
    import argparse
    from pathlib import Path
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=OUT)
    main(parser.parse_args().output)
