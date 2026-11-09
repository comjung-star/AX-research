"""Source-grounded bilingual lexical normalization with cached Dense evidence."""
import json
import unicodedata
from collections import defaultdict
from statistics import mean

from rank_bm25 import BM25Okapi

from ax_research.action_aggregation import purpose_filter
from ax_research.functional_mapping import extract
from ax_research.retrieval.bm25 import KiwiTokenizer
from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate, label_sets


def normalize_scores(values):
    minimum, maximum = min(values), max(values)
    return [(value - minimum) / (maximum - minimum) if maximum > minimum else 0.0 for value in values]


def canonical_tokens(text, rules, config, *, executed=False):
    text = unicodedata.normalize('NFKC', text)
    profile = purpose_filter(extract(text, rules, executed=executed), config)
    return ['function_' + value for value in profile['function_ids']] + ['domain_' + value for value in sorted(profile['domains'])]


def main():
    destination = ROOT / 'docs/improvement-cycle3-20261108-results.json'
    if destination.exists():
        raise FileExistsError(destination)
    rules = read('configs/functional_mapping_20261028.json')
    config = read('configs/action_aggregation_20261102.json')
    registry = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    prior = read('docs/improvement-cycle2-20261108-results.json')
    rankings = [row for row in prior['rankings'] if row['system'] in ('E', 'Dense')]
    ids = sorted(registry)
    assert len(ids) == 112
    tokenizer = KiwiTokenizer()
    documents = ['\n'.join(registry[case][view] for view in ('problem', 'task', 'context')) for case in ids]
    raw_tokens = [tokenizer.tokenize(unicodedata.normalize('NFKC', text)) for text in documents]
    extra_tokens = [canonical_tokens(registry[case]['task'], rules, config, executed=True) for case in ids]
    indexes = {'raw': BM25Okapi(raw_tokens), 'canonical': BM25Okapi([raw + extra for raw, extra in zip(raw_tokens, extra_tokens)])}
    original = {(row['query_id'], row['case_id']): row for row in read('.work-new20-runtime/original/predictions/evidence.json')['records']}
    paths = [row for row in read('.work-new20-runtime/inference/paths.json')['paths'] if row['query_id'].startswith('E_')]
    branches = {}
    with (ROOT / '.work-new20-runtime/inference/branch_scores.jsonl').open(encoding='utf-8') as source:
        for line in source:
            row = json.loads(line)
            if row['path_id'].startswith('E_'):
                branches[row['path_id'], row['case_id']] = row['dense']
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    local_scores = {}
    branch_rankings = []
    coverage = []
    for query, text in list(questions.items()) + [(row['query_id'], row['text']) for row in paths]:
        tokens = tokenizer.tokenize(unicodedata.normalize('NFKC', text))
        canonical = canonical_tokens(text, rules, config)
        coverage.append({'query_id': query, 'canonical_tokens': canonical})
        dense = normalize_scores([original[query, case]['dense'] if query in questions else branches[query, case] for case in ids])
        for mode, index in indexes.items():
            sparse = list(map(float, index.get_scores(tokens + (canonical if mode == 'canonical' else []))))
            normalized = normalize_scores(sparse)
            hybrid = [.5 * left + .5 * right for left, right in zip(dense, normalized)]
            local_scores[query, mode] = hybrid
            if query in questions:
                for name, values in [(mode + '_BM25', sparse), (mode + '_single_hybrid', hybrid)]:
                    ranking = [ids[position] for position in sorted(range(len(ids)), key=lambda position: (-values[position], ids[position]))]
                    for repeat in (1, 2, 3):
                        rankings.append({'query_id': query, 'repeat': repeat, 'system': name, 'ranking': ranking})
            else:
                branch_rankings.append({'path_id': query, 'mode': mode, 'ranking': [ids[position] for position in sorted(range(len(ids)), key=lambda position: (-hybrid[position], ids[position]))]})
    grouped = defaultdict(list)
    for row in paths:
        grouped[row['parent_query_id'], row['repeat'] - 6].append(row['query_id'])
    for (query, repeat), branch_ids in grouped.items():
        assert len(branch_ids) == 3
        for mode in indexes:
            values = [.5 * local_scores[query, mode][position] + .5 * max(local_scores[branch, mode][position] for branch in branch_ids) for position in range(len(ids))]
            ranking = [ids[position] for position in sorted(range(len(ids)), key=lambda position: (-values[position], ids[position]))]
            rankings.append({'query_id': query, 'repeat': repeat, 'system': mode + '_multi_hybrid', 'ranking': ranking})
    results = {name: evaluate(rankings, grades) for name, grades in label_sets().items()}
    output = {'state': 'CYCLE3_EXPLORATORY_LANGUAGE_NORMALIZATION', 'paid_calls': 0, 'test_access': False,
              'results': results, 'rankings': rankings, 'branch_rankings': branch_rankings, 'query_token_coverage': coverage,
              'case_token_coverage': dict(zip(ids, extra_tokens)),
              'limitations': ['No new translations or fresh embeddings', 'Existing grammar may miss core operations',
                              'Validation reused across cycles; no generalization claim', 'Only464 pairs have scoped independent consensus']}
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for label, result in results.items():
        for name, values in result['summary'].items():
            print(label, name, 'F1', round(values['F1@5']['mean'], 5), 'nDCG', round(values['nDCG@10']['mean'], 5))


if __name__ == '__main__':
    main()
