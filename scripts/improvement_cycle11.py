"""Fixed candidate10 formula transferred to preserved CPD development queries."""
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle2 import evaluate
from scripts.improvement_cycle3 import normalize_scores
from scripts.improvement_cycle6 import fidelity_weights
from scripts import improvement_cycle10 as token

BASE = 'docs/core-preserved-three-views-2026-11-07/'
ORIGINAL_CACHE = Path('C:/Users/iovek/OneDrive/문서/ChatGPT/AI공부/AX-core-preserved-20261107-scratch/original/new_query_vectors.npz')


def main():
    destination = ROOT / 'docs/improvement-cycle11-20261108-results.json'
    if destination.exists():
        raise FileExistsError(destination)
    torch.set_num_threads(4)
    torch.manual_seed(20261108)
    cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    ids = sorted(cases)
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / BASE / 'questions.jsonl').read_text(encoding='utf-8').splitlines())}
    paths = [row for row in read(BASE + 'inference/paths.json')['paths'] if row['query_id'].startswith('E_')]
    assert len(questions) == 8 and len(paths) == 72 and len(ids) == 112
    original = {(row['query_id'], row['case_id']): row['dense'] for row in read(BASE + 'original/predictions/evidence.json')['records']}
    branch = {}
    with (ROOT / BASE / 'inference/branch_scores.jsonl').open(encoding='utf-8') as source:
        for line in source:
            row = json.loads(line)
            if row['path_id'].startswith('E_'):
                branch[row['path_id'], row['case_id']] = row['dense']
    cls = {}
    for path in [ROOT / 'docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz', ORIGINAL_CACHE, ROOT / BASE / 'inference/branch_vectors.npz']:
        with np.load(path, allow_pickle=False) as archive:
            cls.update(zip(archive['texts'].tolist(), archive['vectors']))
    with np.load(ROOT / 'docs/stage123-openai-triplicate-2026-10-27/embeddings.npz', allow_pickle=False) as archive:
        positions = {case: position for position, case in enumerate(archive['case_ids'].tolist())}
        matrix = np.asarray([archive['single'][positions[case]] for case in ids])
    for query, text in list(questions.items()) + [(row['query_id'], row['text']) for row in paths]:
        actual = matrix @ cls[text]
        expected = [original[query, case] if query in questions else branch[query, case] for case in ids]
        np.testing.assert_allclose(actual, expected, atol=1e-6)
    token.CACHE = ROOT / '.work-cycle11-token-cache'
    texts = sorted(set(questions.values()) | {row['text'] for row in paths} | {case['task'] for case in cases.values()})
    vectors, manifest = token.encode(texts)
    center = torch.cat([vectors[cases[case]['task']] for case in ids]).mean(dim=0)
    centered = {text: torch.nn.functional.normalize(value - center, dim=1) for text, value in vectors.items()}
    case_tokens = [centered[cases[case]['task']] for case in ids]
    old = read(BASE + 'predictions.json')
    rankings = [{**row, 'system': 'E'} for row in old['systems']['E']]
    hybrid, evidence = {}, []
    for query, text in list(questions.items()) + [(row['query_id'], row['text']) for row in paths]:
        scores = token.token_scores(centered[text], case_tokens)
        dense = [original[query, case] if query in questions else branch[query, case] for case in ids]
        hybrid[query] = np.mean([normalize_scores(scores), normalize_scores(dense)], axis=0)
        evidence.append({'query_id': query, 'centered_maxsim': scores, 'hybrid': hybrid[query].tolist()})
        if query in questions:
            for name, values in [('Dense', dense), ('token_hybrid_single', hybrid[query])]:
                ranking = [ids[position] for position in sorted(range(112), key=lambda position: (-values[position], ids[position]))]
                rankings.extend({'query_id': query, 'repeat': repeat, 'system': name, 'ranking': ranking} for repeat in (1, 2, 3))
    groups = defaultdict(list)
    for row in paths:
        groups[row['parent_query_id'], row['repeat'] - 6].append(row)
    for (query, repeat), local in groups.items():
        assert len(local) == 3
        weights = fidelity_weights([float(cls[questions[query]] @ cls[row['text']]) for row in local])
        scores = .5 * hybrid[query] + .5 * sum(weight * hybrid[row['query_id']] for weight, row in zip(weights, local))
        rankings.append({'query_id': query, 'repeat': repeat, 'system': 'token_hybrid_multi',
                         'ranking': [ids[position] for position in sorted(range(112), key=lambda position: (-scores[position], ids[position]))]})
    all_grades = defaultdict(dict)
    for row in read(BASE + 'labels.json')['records']:
        assert row['case_id'] not in all_grades[row['query_id']]
        all_grades[row['query_id']][row['case_id']] = row['grade']
    eligible = {query: grades for query, grades in all_grades.items() if len(grades) == 112 and all(grade is not None for grade in grades.values())}
    assert len(eligible) == 6 and set(all_grades) - set(eligible) == {'CPD06', 'CPD07'}
    result = evaluate([row for row in rankings if row['query_id'] in eligible], eligible)
    expected_E = .5005050505050505
    assert abs(result['summary']['E']['F1@5']['mean'] - expected_E) < .0001
    inputs = [BASE + 'questions.jsonl', BASE + 'labels.json', BASE + 'inference/paths.json', BASE + 'inference/branch_scores.jsonl',
              'scripts/improvement_cycle11.py', 'docs/improvement-cycle11-20261108-protocol.md', 'scripts/improvement_cycle10.py']
    output = {'state': 'FROZEN_CANDIDATE10_TRANSFER_TO_PREVIOUS_DEVELOPMENT', 'results': result, 'rankings': rankings,
              'score_evidence': evidence, 'eligible_queries': sorted(eligible), 'excluded_incomplete_queries': ['CPD06', 'CPD07'],
              'cache_manifest': manifest, 'case_order': ids, 'paid_calls': 0, 'test_access': False,
              'new_token_texts': len(texts), 'original_dense_reproduction': 8, 'branch_dense_reproduction': 72,
              'original_cls_cache_sha256': token.digest(ORIGINAL_CACHE),
              'input_sha256': {path: token.digest(ROOT / path) for path in inputs},
              'limitations': ['Previous development queries, not independent final test', 'Only6complete-label queries',
                              'AI-Silver labels;29missing grades not imputed', 'Candidate10 frozen; no tuning to transfer results']}
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for name, values in result['summary'].items():
        print(name, 'F1', round(values['F1@5']['mean'], 5), 'nDCG', round(values['nDCG@10']['mean'], 5))


if __name__ == '__main__':
    main()
