"""Replay frozen CPD transfer scores from token caches, not from saved ranks."""
import json
from collections import defaultdict

import numpy as np
import torch

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate
from scripts.improvement_cycle3 import normalize_scores
from scripts.improvement_cycle6 import fidelity_weights
from scripts.improvement_cycle11 import BASE, ORIGINAL_CACHE
from scripts import improvement_cycle10 as token


def main():
    torch.set_num_threads(4)
    artifact = read('docs/improvement-cycle11-20261108-results.json')
    for path, expected in artifact['input_sha256'].items():
        assert token.digest(ROOT / path) == expected, path
    assert token.digest(ORIGINAL_CACHE) == artifact['original_cls_cache_sha256']
    token.CACHE = ROOT / '.work-cycle11-token-cache'
    cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    ids = sorted(cases)
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / BASE / 'questions.jsonl').read_text(encoding='utf-8').splitlines())}
    paths = [row for row in read(BASE + 'inference/paths.json')['paths'] if row['query_id'].startswith('E_')]
    texts = set(questions.values()) | {row['text'] for row in paths} | {case['task'] for case in cases.values()}
    vectors = {}
    for text in texts:
        with np.load(token.token_path(text), allow_pickle=False) as archive:
            vectors[text] = torch.tensor(archive['vectors'].astype(np.float32))
    center = torch.cat([vectors[cases[case]['task']] for case in ids]).mean(dim=0)
    normalized = {text: torch.nn.functional.normalize(value - center, dim=1) for text, value in vectors.items()}
    original = {(row['query_id'], row['case_id']): row['dense'] for row in read(BASE + 'original/predictions/evidence.json')['records']}
    branch = {}
    with (ROOT / BASE / 'inference/branch_scores.jsonl').open(encoding='utf-8') as source:
        for line in source:
            row = json.loads(line)
            if row['path_id'].startswith('E_'):
                branch[row['path_id'], row['case_id']] = row['dense']
    hybrid = {}
    saved_evidence = {row['query_id']: row for row in artifact['score_evidence']}
    for query, text in list(questions.items()) + [(row['query_id'], row['text']) for row in paths]:
        scores = token.token_scores(normalized[text], [normalized[cases[case]['task']] for case in ids])
        dense = [original[query, case] if query in questions else branch[query, case] for case in ids]
        hybrid[query] = np.mean([normalize_scores(scores), normalize_scores(dense)], axis=0)
        np.testing.assert_allclose(scores, saved_evidence[query]['centered_maxsim'], atol=1e-7)
        np.testing.assert_allclose(hybrid[query], saved_evidence[query]['hybrid'], atol=1e-7)
    cls = {}
    for path in [ROOT / 'docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz', ORIGINAL_CACHE, ROOT / BASE / 'inference/branch_vectors.npz']:
        with np.load(path, allow_pickle=False) as archive:
            cls.update(zip(archive['texts'].tolist(), archive['vectors']))
    recovered = [row for row in artifact['rankings'] if row['system'] in ('E', 'Dense')]
    for query in questions:
        ranking = [ids[position] for position in sorted(range(112), key=lambda position: (-hybrid[query][position], ids[position]))]
        recovered.extend({'query_id': query, 'repeat': repeat, 'system': 'token_hybrid_single', 'ranking': ranking} for repeat in (1, 2, 3))
    grouped = defaultdict(list)
    for row in paths:
        grouped[row['parent_query_id'], row['repeat'] - 6].append(row)
    for (query, repeat), branches in grouped.items():
        weights = fidelity_weights([float(cls[questions[query]] @ cls[row['text']]) for row in branches])
        scores = .5 * hybrid[query] + .5 * sum(weight * hybrid[row['query_id']] for weight, row in zip(weights, branches))
        ranking = [ids[position] for position in sorted(range(112), key=lambda position: (-scores[position], ids[position]))]
        recovered.append({'query_id': query, 'repeat': repeat, 'system': 'token_hybrid_multi', 'ranking': ranking})
    saved = {(row['query_id'], row['repeat'], row['system']): row['ranking'] for row in artifact['rankings']}
    assert len(saved) == len(recovered) == 96
    for row in recovered:
        assert row['ranking'] == saved[row['query_id'], row['repeat'], row['system']]
    grades = defaultdict(dict)
    for row in read(BASE + 'labels.json')['records']:
        grades[row['query_id']][row['case_id']] = row['grade']
    eligible = {query: values for query, values in grades.items() if all(value is not None for value in values.values())}
    recomputed = evaluate([row for row in recovered if row['query_id'] in eligible], eligible)
    assert recomputed == artifact['results']
    verification = {'state': 'ALL_TRANSFER_TOKEN_SCORES_CANDIDATE_RANKINGS_AND_METRICS_REPRODUCED',
                    'score_groups': len(hybrid), 'new_candidate_rankings': 48, 'complete_label_queries': 6,
                    'excluded_incomplete_queries': ['CPD06', 'CPD07'], 'paid_calls': 0, 'test_access': False}
    with (ROOT / 'docs/improvement-cycle11-20261108-verification.json').open('x', encoding='utf-8') as target:
        target.write(json.dumps(verification, indent=2) + '\n')
    print(json.dumps(verification))


if __name__ == '__main__':
    main()
