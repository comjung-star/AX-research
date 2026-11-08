"""Matched-budget cached mapping-order replay; never fresh model inference."""
import hashlib
import json
import math
import random
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/autonomous-improvement-20261108'


def read(path):
    return json.loads((ROOT / path).read_text(encoding='utf-8'))


def handoff(dense, sparse, count=20):
    if len(set(dense)) != len(dense) or len(set(sparse)) != len(sparse) or set(dense) != set(sparse):
        raise ValueError('Candidate source registries differ or contain duplicates')
    selected = []
    for pair in zip(dense, sparse):
        for case_id in pair:
            if case_id not in selected:
                selected.append(case_id)
            if len(selected) == count:
                return selected
    raise ValueError('Insufficient candidates')


def restrict(ranking, candidates):
    if len(set(ranking)) != len(ranking) or not set(candidates) <= set(ranking):
        raise ValueError('Invalid mapping ranking or candidate handoff')
    return [case_id for case_id in ranking if case_id in set(candidates)]


def metrics(ranking, grades):
    positive = sum(grade >= 2 for grade in grades.values())
    hits = sum(grades[case_id] >= 2 for case_id in ranking[:5])
    if not positive:
        return {'P@5': hits / 5, 'F1@5': None, 'nDCG@10': None}
    ideal = sorted(grades.values(), reverse=True)[:10]
    dcg = lambda values: sum((2 ** grade - 1) / math.log2(index + 2)
                             for index, grade in enumerate(values))
    return {'P@5': hits / 5, 'F1@5': 2 * hits / (5 + positive),
            'nDCG@10': dcg([grades[case_id] for case_id in ranking[:10]]) / dcg(ideal)}


def interval(values):
    generator = random.Random(20261108)
    samples = sorted(mean(generator.choices(values, k=len(values))) for _ in range(10000))
    return [samples[249], samples[9749]]


def main():
    paths = ['docs/validation-new20-20261107/diagnosis/raw_search_stage_rankings.json',
             'docs/validation-new20-20261107/measured/predictions_new20.json',
             'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json']
    ranks, predictions, labels = map(read, paths)
    assert len(ranks['questions']) == 20 and len(ranks['case_ids']) == 112
    by_system = {name: {row['query_id']: row['ranking'] for row in rows}
                 for name, rows in ranks['systems'].items()}
    grades = {query: {} for query in ranks['questions']}
    for row in labels['records']:
        assert row['case_id'] not in grades[row['query_id']]
        grades[row['query_id']][row['case_id']] = row['grade']
    assert all(set(value) == set(ranks['case_ids']) for value in grades.values())
    per_query = []
    outputs = []
    for query in ranks['questions']:
        proposed = handoff(by_system['Dense'][query], by_system['BM25'][query])
        baseline = by_system['Hybrid_RRF'][query][:20]
        rows = [row for row in predictions['systems']['E'] if row['query_id'] == query]
        assert len(rows) == 3
        values = {'baseline': [], 'proposed': []}
        for row in rows:
            assert len(row['ranking']) == 112 and set(row['ranking']) == set(ranks['case_ids'])
            for name, candidates in [('baseline', baseline), ('proposed', proposed)]:
                ranking = restrict(row['ranking'], candidates)
                assert len(ranking) == 20
                values[name].append(metrics(ranking, grades[query]))
                outputs.append({'query_id': query, 'repeat': row['repeat'], 'policy': name,
                                'candidate_ids': candidates, 'ranking': ranking,
                                'candidate_provenance': {case_id: {
                                    'dense_rank': by_system['Dense'][query].index(case_id) + 1,
                                    'sparse_rank': by_system['BM25'][query].index(case_id) + 1}
                                    for case_id in candidates}})
        per_query.append({'query_id': query, 'positive_count': sum(g >= 2 for g in grades[query].values()),
                          **{name: {metric: mean(value[metric] for value in repeats)
                                    if repeats[0][metric] is not None else None
                                    for metric in repeats[0]} for name, repeats in values.items()}})
    summary = {}
    for metric in ('P@5', 'F1@5', 'nDCG@10'):
        eligible = [row for row in per_query if row['baseline'][metric] is not None]
        deltas = [row['proposed'][metric] - row['baseline'][metric] for row in eligible]
        summary[metric] = {'query_count': len(eligible),
                           **{name: mean(row[name][metric] for row in eligible)
                              for name in ('baseline', 'proposed')},
                           'paired_delta': mean(deltas), 'paired_bootstrap95': interval(deltas)}
    result = {'state': 'CACHED_MAPPING_ORDER_REPLAY_ONLY', 'summary': summary,
              'per_query': per_query, 'rankings': outputs,
              'limitations': ['No new precision-mapping execution or fresh embedding inference.',
                              'E preserves historical multi-perspective final ordering including historical retrieval tie breaks.',
                              'Restriction is equivalent only for candidate-independent scores and unchanged tie breaks; not a full architecture claim.',
                              'Equal-20 interleaving is post-hoc, not the preregistered unequal union endpoint.',
                              'Provisional labels; no independent ground truth; not an efficacy claim.'],
              'input_sha256': {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths},
              'script_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'paid_api_usd': 0, 'official_trial_completed': False,
              'sealed_test_opened': False, 'bootstrap_unit': 'query; average 3 stored repeats first',
              'zero_positive_policy': 'F1/nDCG undefined and excluded; P@5 reported across all20'}
    target = OUT / '14_work_mapping_order_replay.json'
    if target.exists():
        assert json.loads(target.read_text(encoding='utf-8')) == result
    else:
        target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'state': result['state'], 'summary': summary}, ensure_ascii=False))


if __name__ == '__main__':
    main()
