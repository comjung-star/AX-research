"""Offline component ablation with frozen evidence and labels."""
import hashlib
import json
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from statistics import mean

from ax_research.action_aggregation import compose, purpose_filter
from ax_research.functional_mapping import compare, extract
from scripts.autonomous_trial2_mapping_replay import interval, metrics

ROOT = Path(__file__).resolve().parents[1]


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding='utf-8'))


def main():
    destination = ROOT / 'docs/improvement-cycle-20261108-results.json'
    if destination.exists():
        raise FileExistsError(destination)
    runtime = '.work-new20-runtime/'
    original = read(runtime + 'original/predictions/evidence.json')['records']
    whole = {(row['query_id'], row['case_id']): row for row in original}
    branches = {}
    with (ROOT / runtime / 'inference/branch_scores.jsonl').open(encoding='utf-8') as source:
        for line in source:
            row = json.loads(line)
            if row['path_id'].startswith('E_'):
                branches[row['path_id'], row['case_id']] = row
    groups = defaultdict(list)
    for row in read(runtime + 'inference/paths.json')['paths']:
        if row['query_id'].startswith('E_'):
            groups[row['parent_query_id'], row['repeat'] - 6].append(row['query_id'])
    historical = read('docs/validation-new20-20261107/measured/predictions_new20.json')
    rules = read('configs/functional_mapping_20261028.json')
    config = read('configs/action_aggregation_20261102.json')
    cases = read('docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json')
    filtered = {case: {role: purpose_filter(profile, config) for role, profile in roles.items()} for case, roles in cases.items()}
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    ids = historical['case_ids']
    rankings = []
    for (query, repeat), paths in sorted(groups.items()):
        assert len(paths) == 3
        profile = purpose_filter(extract(questions[query], rules), config)
        scores = defaultdict(dict)
        ties = {}
        for case in ids:
            record = whole[query, case]
            evidence = [branches[path, case] for path in paths]
            whole_grade = compare(profile, filtered[case])['mapping_grade']
            branch_grades = {path: branches[path, case]['C1_rule']['mapping_grade'] for path in paths}
            branch_semantic = {path: branches[path, case]['semantic']['score'] for path in paths}
            semantic = record['semantic']['score']
            composition = compose(whole_grade, branch_grades, semantic, branch_semantic)
            scores['E'][case] = composition['score']
            scores['no_rules'][case] = composition['embedding_contribution']
            scores['original_rules_only'][case] = .5 * whole_grade / 4 + composition['embedding_contribution']
            scores['no_branch_semantic'][case] = composition['rule_contribution'] + .5 * (semantic + 1) / 2
            averaged = (semantic + mean(branch_semantic.values())) / 2
            scores['mean_branch_semantic'][case] = composition['rule_contribution'] + .5 * (averaged + 1) / 2
            scores['Dense'][case] = record['dense']
            ties[case] = mean(Fraction(row['hybrid_exact']) for row in evidence)
        reproduced = sorted(ids, key=lambda case: (-scores['E'][case], -ties[case], case))
        expected = next(row['ranking'] for row in historical['systems']['E']
                        if row['query_id'] == query and row['repeat'] == repeat)
        assert reproduced == expected, (query, repeat)
        for name, values in scores.items():
            ranking = sorted(ids, key=lambda case: (-values[case], -ties[case] if name != 'Dense' else 0, case))
            rankings.append({'query_id': query, 'repeat': repeat, 'system': name, 'ranking': ranking})
    label_paths = {
        'working_transfer': 'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json',
        'original': 'docs/validation-new20-20261107/measured/labels_new20.json',
    }
    results = {}
    for label_name, label_path in label_paths.items():
        raw = read(label_path)
        label_rows = raw['records'] if 'records' in raw else raw['ratings']
        grades = defaultdict(dict)
        for row in label_rows:
            grades[row['query_id']][row['case_id']] = row['grade']
        assert len(grades) == 20 and all(len(values) == 112 for values in grades.values())
        values = defaultdict(lambda: defaultdict(list))
        for row in rankings:
            values[row['query_id']][row['system']].append(metrics(row['ranking'], grades[row['query_id']]))
        averaged = {query: {name: {metric: mean(item[metric] for item in repeats) if repeats[0][metric] is not None else None
                                  for metric in repeats[0]} for name, repeats in systems.items()}
                    for query, systems in values.items()}
        summary = {}
        for name in next(iter(averaged.values())):
            summary[name] = {}
            for metric in ('P@5', 'F1@5', 'nDCG@10'):
                eligible = [systems for systems in averaged.values() if systems[name][metric] is not None]
                summary[name][metric] = {'queries': len(eligible), 'mean': mean(row[name][metric] for row in eligible)}
                for baseline in ('E', 'Dense'):
                    differences = [row[name][metric] - row[baseline][metric] for row in eligible]
                    summary[name][metric][baseline] = {'delta': mean(differences), 'interval95': interval(differences)}
        results[label_name] = {'summary': summary, 'per_query': averaged,
                               'labels_sha256': hashlib.sha256((ROOT / label_path).read_bytes()).hexdigest()}
    output = {'state': 'EXPLORATORY_CACHED_SCORE_ABLATION', 'exact_E_reproduction_groups': len(groups),
              'paid_calls': 0, 'test_access': False, 'results': results, 'rankings': rankings}
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for label, result in results.items():
        for name, values in result['summary'].items():
            print(label, name, 'F1', round(values['F1@5']['mean'], 5), 'nDCG', round(values['nDCG@10']['mean'], 5))


if __name__ == '__main__':
    main()
