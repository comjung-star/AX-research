"""Query-grounded branch and equal-budget candidate diagnostics, no API calls."""
import hashlib
import json
from collections import defaultdict
from fractions import Fraction
from statistics import mean

from ax_research.action_aggregation import allowed_branches, compose, purpose_filter
from ax_research.functional_mapping import compare, extract
from scripts.improvement_cycle import ROOT, read
from scripts.autonomous_trial2_mapping_replay import handoff, interval, metrics


def evaluate(rankings, grades):
    grouped = defaultdict(lambda: defaultdict(list))
    for row in rankings:
        query_grades = grades[row['query_id']]
        values = metrics(row['ranking'], query_grades)
        positives = sum(grade >= 2 for grade in query_grades.values())
        values['Recall@20'] = sum(query_grades[case] >= 2 for case in row['ranking'][:20]) / positives if positives else None
        grouped[row['query_id']][row['system']].append(values)
    averaged = {query: {name: {metric: mean(item[metric] for item in repeats) if repeats[0][metric] is not None else None
                              for metric in repeats[0]} for name, repeats in systems.items()}
                for query, systems in grouped.items()}
    summary = {}
    for name in next(iter(averaged.values())):
        summary[name] = {}
        for metric in ('P@5', 'F1@5', 'nDCG@10', 'Recall@20'):
            eligible = [systems for systems in averaged.values() if systems[name][metric] is not None]
            summary[name][metric] = {'queries': len(eligible), 'mean': mean(row[name][metric] for row in eligible)}
            if metric in ('F1@5', 'nDCG@10'):
                for baseline in ('E', 'Dense'):
                    differences = [row[name][metric] - row[baseline][metric] for row in eligible]
                    summary[name][metric][baseline] = {'delta': mean(differences), 'interval95': interval(differences)}
    return {'summary': summary, 'per_query': averaged}


def label_sets():
    labels = {}
    paths = {'working_transfer': 'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json',
             'original': 'docs/validation-new20-20261107/measured/labels_new20.json'}
    for name, path in paths.items():
        raw = read(path)
        rows = raw['records'] if 'records' in raw else raw['ratings']
        grades = defaultdict(dict)
        for row in rows:
            assert row['case_id'] not in grades[row['query_id']]
            grades[row['query_id']][row['case_id']] = row['grade']
        assert len(grades) == 20 and all(len(values) == 112 for values in grades.values())
        labels[name] = grades
    overlay = {query: dict(values) for query, values in labels['working_transfer'].items()}
    review = read('docs/autonomous-improvement-20261108/19_independent_adjudication_and_stop_decision.json')
    assert len(review['rows']) == 464
    for row in review['rows']:
        assert row['adjudication'] in ('POSITIVE', 'NEGATIVE')
        overlay[row['query_id']][row['case_id']] = row['conservative_grade']
    labels['scoped_consensus_464_only'] = overlay
    return labels


def main():
    destination = ROOT / 'docs/improvement-cycle2-20261108-results.json'
    if destination.exists():
        raise FileExistsError(destination)
    prior = read('docs/improvement-cycle-20261108-results.json')
    rankings = [row for row in prior['rankings'] if row['system'] in ('E', 'Dense', 'original_rules_only')]
    by_key = {(row['query_id'], row['repeat'], row['system']): row['ranking'] for row in rankings}
    rules = read('configs/functional_mapping_20261028.json')
    config = read('configs/action_aggregation_20261102.json')
    cases = read('docs/query-case-functional-mapping-2026-10-28/stage2/case_profiles.json')
    filtered = {case: {role: purpose_filter(profile, config) for role, profile in roles.items()} for case, roles in cases.items()}
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    runtime = '.work-new20-runtime/'
    whole = {(row['query_id'], row['case_id']): row for row in read(runtime + 'original/predictions/evidence.json')['records']}
    paths = read(runtime + 'inference/paths.json')['paths']
    groups = defaultdict(list)
    for row in paths:
        if row['query_id'].startswith('E_'):
            groups[row['parent_query_id'], row['repeat'] - 6].append(row)
    branches = {}
    with (ROOT / runtime / 'inference/branch_scores.jsonl').open(encoding='utf-8') as source:
        for line in source:
            row = json.loads(line)
            if row['path_id'].startswith('E_'):
                branches[row['path_id'], row['case_id']] = row
    diagnostics = []
    for (query, repeat), views in sorted(groups.items()):
        ids = by_key[query, repeat, 'Dense']
        sparse = sorted(ids, key=lambda case: (-whole[query, case]['bm25'], case))
        candidate_sets = {'dense20': ids[:20], 'alternate20': handoff(ids, sparse)}
        for policy, candidates in candidate_sets.items():
            assert len(candidates) == len(set(candidates)) == 20
            for scorer in ('E', 'original_rules_only'):
                ranking = [case for case in by_key[query, repeat, scorer] if case in candidates]
                rankings.append({'query_id': query, 'repeat': repeat, 'system': policy + '_' + scorer, 'ranking': ranking})
        profile = purpose_filter(extract(questions[query], rules), config)
        profiles = {view['query_id']: purpose_filter(extract(view['text'], rules), config) for view in views}
        lexical = {path for path, value in profiles.items() if set(profile['function_ids']) & set(value['function_ids'])}
        scores = defaultdict(dict)
        ties = {}
        for case in ids:
            evidence = {path: branches[path, case] for path in profiles}
            original_grade = compare(profile, filtered[case])['mapping_grade']
            grades = {path: row['C1_rule']['mapping_grade'] for path, row in evidence.items()}
            semantics = {path: row['semantic']['score'] for path, row in evidence.items()}
            original_semantic = whole[query, case]['semantic']['score']
            allowed = allowed_branches(profile, profiles, filtered[case]['task'])
            gated = compose(original_grade, grades, original_semantic, semantics, allowed)
            scores['case_core_gate'][case] = gated['score']
            scores['case_core_gate_original_rules'][case] = .5 * original_grade / 4 + gated['embedding_contribution']
            scores['query_core_gate'][case] = compose(original_grade, grades, original_semantic, semantics, lexical)['score']
            ties[case] = mean(Fraction(row['hybrid_exact']) for row in evidence.values())
        diagnostics.append({'query_id': query, 'repeat': repeat, 'original_functions': profile['function_ids'],
                            'branch_functions': {path: value['function_ids'] for path, value in profiles.items()},
                            'query_grounded_branches': sorted(lexical)})
        for name, values in scores.items():
            rankings.append({'query_id': query, 'repeat': repeat, 'system': name,
                             'ranking': sorted(ids, key=lambda case: (-values[case], -ties[case], case))})
    results = {name: evaluate(rankings, grades) for name, grades in label_sets().items()}
    output = {'state': 'CYCLE2_EXPLORATORY_CACHED_ABLATION', 'paid_calls': 0, 'test_access': False,
              'prior_sha256': hashlib.sha256((ROOT / 'docs/improvement-cycle-20261108-results.json').read_bytes()).hexdigest(),
              'results': results, 'diagnostics': diagnostics, 'rankings': rankings,
              'limits': ['No fresh independent test', '464-pair overlay is partial independent AI review, not full gold',
                         'Frozen 18-rule grammar may fail to recognize real core functions',
                         'Descriptive intervals do not adjust for development selection']}
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for label, result in results.items():
        for name, values in result['summary'].items():
            print(label, name, 'F1', round(values['F1@5']['mean'], 5), 'nDCG', round(values['nDCG@10']['mean'], 5))


if __name__ == '__main__':
    main()
