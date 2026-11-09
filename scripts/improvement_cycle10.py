"""Offline contextual token matching from the existing frozen local backbone."""
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

import numpy as np
import torch

from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle3 import normalize_scores
from scripts.improvement_cycle6 import fidelity_weights

MODEL = Path('C:/Users/iovek/OneDrive/문서/ChatGPT/AI공부/AX-prototype/.local/models/bge-m3')
CACHE = ROOT / '.work-cycle10-token-cache'


def digest(path):
    checksum = hashlib.sha256()
    with path.open('rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            checksum.update(chunk)
    return checksum.hexdigest()


def token_path(text):
    return CACHE / (hashlib.sha256(text.encode('utf-8')).hexdigest() + '.npz')


def encode(texts):
    for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY'):
        os.environ[key] = '1'
    expected = read('docs/core-preserved-three-views-2026-11-07/preregistration.json')['environment']['model']
    actual = {name: digest(MODEL / name) for name in expected}
    assert actual == expected, 'Frozen local model mismatch'
    CACHE.mkdir(exist_ok=True)
    manifest_path = CACHE / 'manifest.json'
    manifest = {'model_hashes': actual, 'method': 'last_hidden_state_no_special_tokens_float16',
                'input_text_sha256': sorted(hashlib.sha256(text.encode('utf-8')).hexdigest() for text in texts)}
    if manifest_path.exists():
        assert json.loads(manifest_path.read_text(encoding='utf-8')) == manifest
    else:
        manifest_path.write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    missing = [text for text in texts if not token_path(text).exists()]
    if missing:
        from transformers import AutoModel, AutoTokenizer
        tokenizer = AutoTokenizer.from_pretrained(str(MODEL), local_files_only=True)
        model = AutoModel.from_pretrained(str(MODEL), local_files_only=True)
        model.eval()
        tokenized = {text: tokenizer(text, return_special_tokens_mask=True, truncation=False) for text in missing}
        assert max(len(item['input_ids']) for item in tokenized.values()) <= 4096, 'No truncation permitted'
        ordered = sorted(missing, key=lambda text: len(tokenized[text]['input_ids']))
        with torch.inference_mode():
            for start in range(0, len(ordered), 4):
                batch_texts = ordered[start:start + 4]
                batch = tokenizer.pad([tokenized[text] for text in batch_texts], padding=True, return_tensors='pt')
                hidden = model(input_ids=batch['input_ids'], attention_mask=batch['attention_mask']).last_hidden_state
                for position, text in enumerate(batch_texts):
                    mask = batch['attention_mask'][position].bool() & ~batch['special_tokens_mask'][position].bool()
                    vectors = hidden[position][mask].cpu().numpy().astype(np.float16)
                    tokens = batch['input_ids'][position][mask].cpu().numpy()
                    assert len(vectors) > 0 and np.isfinite(vectors).all()
                    with token_path(text).open('xb') as target:
                        np.savez_compressed(target, vectors=vectors, token_ids=tokens)
                print(json.dumps({'encoded_texts': min(start + 4, len(ordered)), 'missing_texts': len(ordered)}), flush=True)
        del model
    vectors = {}
    for text in texts:
        with np.load(token_path(text), allow_pickle=False) as archive:
            values = torch.tensor(archive['vectors'].astype(np.float32))
            assert values.ndim == 2 and values.shape[1] == 1024 and torch.isfinite(values).all()
            vectors[text] = values
    return vectors, manifest


def token_scores(query, case_tokens):
    lengths = [len(values) for values in case_tokens]
    matrix = torch.cat(case_tokens)
    similarities = query @ matrix.T
    return [float(part.max(dim=1).values.mean()) for part in similarities.split(lengths, dim=1)]


def main():
    destination = ROOT / 'docs/improvement-cycle10-20261108-results.json'
    if destination.exists():
        raise FileExistsError(destination)
    torch.set_num_threads(4)
    torch.manual_seed(20261108)
    cases = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    ids = sorted(cases)
    questions = {row['query_id']: row['text'] for row in map(json.loads, (ROOT / 'docs/validation-new20-20261107/questions.jsonl').read_text(encoding='utf-8').splitlines())}
    paths = [row for row in read('.work-new20-runtime/inference/paths.json')['paths'] if row['query_id'].startswith('E_')]
    texts = sorted(set(questions.values()) | {row['text'] for row in paths} | {case['task'] for case in cases.values()})
    vectors, manifest = encode(texts)
    raw_cases = [vectors[cases[case]['task']] for case in ids]
    center = torch.cat(raw_cases).mean(dim=0)
    normalized = {text: torch.nn.functional.normalize(values, dim=1) for text, values in vectors.items()}
    centered = {text: torch.nn.functional.normalize(values - center, dim=1) for text, values in vectors.items()}
    centered_cases = [centered[cases[case]['task']] for case in ids]
    original_dense = {(row['query_id'], row['case_id']): row['dense'] for row in read('.work-new20-runtime/original/predictions/evidence.json')['records']}
    branch_dense = {}
    with (ROOT / '.work-new20-runtime/inference/branch_scores.jsonl').open(encoding='utf-8') as source:
        for line in source:
            row = json.loads(line)
            if row['path_id'].startswith('E_'):
                branch_dense[row['path_id'], row['case_id']] = row['dense']
    cls = {}
    for path in ['docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz',
                 'validation20-scratch/original/new_query_vectors.npz', '.work-new20-runtime/inference/branch_vectors.npz']:
        with np.load(ROOT / path, allow_pickle=False) as archive:
            cls.update(zip(archive['texts'].tolist(), archive['vectors']))
    rankings = [row for row in read('docs/improvement-cycle9-20261108-results.json')['rankings'] if row['system'] in ('E', 'Dense')]
    hybrid, score_evidence = {}, []
    for query, text in list(questions.items()) + [(row['query_id'], row['text']) for row in paths]:
        scores = token_scores(centered[text], centered_cases)
        dense = [original_dense[query, case] if query in questions else branch_dense[query, case] for case in ids]
        hybrid[query] = np.mean([normalize_scores(scores), normalize_scores(dense)], axis=0)
        score_evidence.append({'query_id': query, 'centered_maxsim': scores, 'hybrid': hybrid[query].tolist()})
        if query in questions:
            raw = token_scores(normalized[text], [normalized[cases[case]['task']] for case in ids])
            for name, values in [('raw_token_single', raw), ('centered_token_single', scores), ('token_hybrid_single', hybrid[query])]:
                ranking = [ids[position] for position in sorted(range(112), key=lambda position: (-values[position], ids[position]))]
                for repeat in (1, 2, 3):
                    rankings.append({'query_id': query, 'repeat': repeat, 'system': name, 'ranking': ranking})
    groups = defaultdict(list)
    for row in paths:
        groups[row['parent_query_id'], row['repeat'] - 6].append(row)
    for (query, repeat), branches in groups.items():
        weights = fidelity_weights([float(np.dot(cls[questions[query]], cls[row['text']])) for row in branches])
        values = .5 * hybrid[query] + .5 * sum(weight * hybrid[row['query_id']] for weight, row in zip(weights, branches))
        rankings.append({'query_id': query, 'repeat': repeat, 'system': 'token_hybrid_multi',
                         'ranking': [ids[position] for position in sorted(range(112), key=lambda position: (-values[position], ids[position]))]})
    from scripts.improvement_cycle2 import evaluate, label_sets
    results = {name: evaluate(rankings, grades) for name, grades in label_sets().items()}
    output = {'state': 'FREE_LOCAL_CONTEXTUAL_TOKEN_MATCHING_DEVELOPMENT', 'results': results, 'rankings': rankings,
              'score_evidence': score_evidence, 'case_order': ids, 'cache_manifest': manifest,
              'paid_calls': 0, 'test_access': False, 'new_embedding_texts': len(texts),
              'script_sha256': digest(Path(__file__)), 'protocol_sha256': digest(ROOT / 'docs/improvement-cycle10-20261108-protocol.md'),
              'limits': ['Not trained ColBERT or cross-encoder; raw backbone token experiment',
                         'Repeatedly inspected development queries, no independent-test claim', 'Evaluation labels unchanged']}
    destination.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for label, result in results.items():
        for name, values in result['summary'].items():
            print(label, name, 'F1', round(values['F1@5']['mean'], 5), 'nDCG', round(values['nDCG@10']['mean'], 5))


if __name__ == '__main__':
    main()
