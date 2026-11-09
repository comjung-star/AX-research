"""Contract-gate first, freeze, then one fixed-weight question-only ablation."""
import argparse
import json
import os
from statistics import mean
import zipfile

import numpy as np

from ax_research.query_understanding_v2 import understand
from ax_research.frozen_ensemble import mean_fold_scores
from ax_research.pairwise_ridge import rank_pool, score
from scripts.check_query_understanding_v2 import check_contracts
from scripts.improvement_cycle import ROOT, read
from scripts.task_alignment_20261109 import MODEL, sha
from scripts.transfer40_work_aligned_20261109 import build_features
from scripts.autonomous_trial2_mapping_replay import interval

OUT = ROOT / 'docs/query-understanding-v2-20261109'
SOURCES = ['src/ax_research/query_understanding_v2.py', 'configs/query_understanding_v2_contracts.json',
           'scripts/check_query_understanding_v2.py', 'scripts/query_understanding_v2_experiment.py',
           'docs/query-understanding-v2-20261109-protocol.md', 'configs/semantic_mapping_20261028.json',
           'src/ax_research/semantic_mapping.py', 'src/ax_research/task_alignment.py',
           'src/ax_research/pairwise_ridge.py', 'src/ax_research/frozen_ensemble.py',
           'scripts/transfer40_work_aligned_20261109.py', 'docs/task-alignment-reference-20261109/config.json']


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as target:
        target.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def gate():
    if OUT.exists():
        raise FileExistsError(OUT)
    result = check_contracts()
    assert result['passed'], [r for r in result['rows'] if not r['passed']]
    OUT.mkdir()
    write('extraction-gate.json', result)
    with zipfile.ZipFile(OUT / 'source-snapshot.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in SOURCES:
            archive.write(ROOT / path, arcname=path)
    write('freeze.json', {'version': 'query-understanding-v2-20261109',
        'gate_passed': True, 'source_sha256': {p: sha(ROOT / p) for p in SOURCES},
        'gate_sha256': sha(OUT / 'extraction-gate.json'), 'snapshot_sha256': sha(OUT / 'source-snapshot.zip'),
        'relevance_scores_read_during_gate': False, 'human_gold': False, 'new_training': False,
        'policy': '20 uses original heldout-fold weights; 40 uses original five-model arithmetic score mean'})
    print('GATE_PASS_AND_FROZEN', result['cases'], 'contracts')


def frozen():
    freeze = load('freeze.json')
    assert all(sha(ROOT / p) == h for p, h in freeze['source_sha256'].items())
    assert sha(OUT / 'extraction-gate.json') == freeze['gate_sha256']
    assert sha(OUT / 'source-snapshot.zip') == freeze['snapshot_sha256']
    return freeze


def infer():
    frozen()
    import sys, socket
    accesses = []
    def audit(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = str(args[0]).replace('\\', '/').lower()
            if any(s in path for s in ('blind_review', '/qrels', 'labels_new20', 'ai_consensus.json', '.ax-heldout', 'heldout-final-resume')):
                raise RuntimeError('No relevance or final-test input during inference')
            if path.endswith(('.json', '.jsonl', '.npz')):
                accesses.append(str(args[0]))
    sys.addaudithook(audit)
    def blocked(*args, **kwargs):
        raise RuntimeError('Local-only inference')
    socket.socket.connect = blocked
    socket.create_connection = blocked
    config = read('configs/semantic_mapping_20261028.json')
    models = read('docs/task-alignment-reference-20261109/config.json')
    old20 = read('docs/task-alignment-20261109-inputs.json')
    old40 = read('docs/transfer40-work-aligned-20261109/inputs.json')
    cases = read('docs/literal-action-recovery-20261109/case_profiles.json')
    data = {}
    for scope, old in [('dev20', old20), ('reuse40', old40)]:
        parsed = {q: understand(p['source_text'], config) for q, p in old['partitions'].items()}
        data[scope] = {'old': old, 'partitions': {q: v[0] for q, v in parsed.items()}, 'profiles': {q: v[1] for q, v in parsed.items()}}
    texts = {v for row in data.values() for profile in row['profiles'].values() for v in profile['fields'].values() if v}
    texts |= {p[f] for row in data.values() for p in row['partitions'].values() for f in ('excluded_text', 'output_hint_text') if p[f]}
    texts |= {v for p in cases.values() for v in p['fields'].values() if v}
    banks = ['docs/query-case-semantic-mapping-2026-10-28/mapping/embeddings.npz',
             'docs/task-alignment-20261109-vectors.npz', 'docs/transfer40-work-aligned-20261109/vectors.npz']
    bank = {}
    for path in banks:
        with np.load(ROOT / path, allow_pickle=False) as z:
            for text, vector in zip(z['texts'].tolist(), z['vectors']):
                bank.setdefault(text, vector)
    missing = sorted(texts - set(bank))
    assert all(sha(MODEL / p) == h for p, h in models['model_sha256'].items())
    print('LOCAL_ENCODING', len(missing), 'field strings', flush=True)
    if missing:
        for key in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_HUB_DISABLE_TELEMETRY'):
            os.environ[key] = '1'
        import torch
        from sentence_transformers import SentenceTransformer
        torch.set_num_threads(4)
        torch.manual_seed(20261028)
        torch.use_deterministic_algorithms(True)
        encoder = SentenceTransformer(str(MODEL), device='cpu', local_files_only=True)
        encoder.max_seq_length = 4096
        assert max(len(encoder.tokenizer.encode(t)) for t in missing) <= 4096
        vectors = encoder.encode(missing, batch_size=8, normalize_embeddings=True, convert_to_numpy=True, show_progress_bar=False)
        bank.update(zip(missing, vectors.astype(np.float32)))
        del encoder
    selected = sorted(texts)
    array = np.array([bank[t] for t in selected], dtype=np.float32)
    assert np.isfinite(array).all() and np.allclose(np.linalg.norm(array, axis=1), 1, atol=1e-5)
    vector_path = OUT / 'vectors.npz'
    if vector_path.exists():
        raise FileExistsError(vector_path)
    np.savez_compressed(vector_path, texts=np.array(selected), vectors=array)
    for scope, value in data.items():
        old, profiles, partitions = value['old'], value['profiles'], value['partitions']
        ids = old['ids']
        original_path = 'docs/task-alignment-20261109-predictions.json' if scope == 'dev20' else 'docs/transfer40-work-aligned-20261109/predictions.json'
        original = read(original_path)
        rankings = []
        for r in original['rankings']:
            prefix = 'WorkAligned_' if scope == 'dev20' else 'Aligned_'
            if r['system'].startswith(prefix):
                rankings.append({**r, 'system': r['system'].replace(prefix, 'V1_', 1)})
            elif r['system'] in ('Dense', 'BM25', 'E'):
                rankings.append(r)
        inputs = {}
        for q, row in old['inputs'].items():
            if scope == 'dev20':
                base = np.array(row['features'])
                maps = [dict(zip(ids, base[:, index])) for index in (0, 1, 2)]
                dense_order = row['dense']
            else:
                maps = [row[name] for name in ('dense', 'token', 'sparse')]
                dense_order = row['dense_order']
            features = build_features(ids, *maps, profiles[q], partitions[q], cases, bank)
            if scope == 'dev20':
                fold = old['outer_folds'][q]
                model = next(m for m in models['fold_models'] if m['outer_fold'] == fold)
                scores = score(features, np.array(model['weights']), model['learned_share'])
            else:
                scores = mean_fold_scores(features, models['fold_models'])
            inputs[q] = {'features': features.tolist(), 'scores': scores.tolist(), 'maps': maps,
                         'dense_order': dense_order, 'pools': row['pools']}
            for repeat in (1, 2, 3):
                for pool, candidates in row['pools'][str(repeat)].items():
                    rankings.append({'query_id': q, 'repeat': repeat, 'system': 'V2_' + pool,
                                     'ranking': rank_pool(ids, scores, candidates, dense_order)})
        write(scope + '-inputs.json', {'ids': ids, 'inputs': inputs, 'profiles': profiles, 'partitions': partitions,
             'source_inputs_sha256': sha(ROOT / ('docs/task-alignment-20261109-inputs.json' if scope == 'dev20' else 'docs/transfer40-work-aligned-20261109/inputs.json'))})
        write(scope + '-predictions.json', {'rankings': rankings, 'source_prediction_sha256': sha(ROOT / original_path),
             'input_sha256': sha(OUT / (scope + '-inputs.json')), 'freeze_sha256': sha(OUT / 'freeze.json'),
             'new_training': False, 'labels_read': False, 'test15_read': False})
        print('SEALED', scope, len(rankings), 'rankings', flush=True)
    write('inference.json', {'state': 'PREDICTIONS_FROZEN_BEFORE_LABEL_EVALUATION', 'paid_calls': 0,
                            'new_training': False, 'new_field_strings': len(missing), 'vectors_sha256': sha(vector_path),
                            'banks_sha256': {p: sha(ROOT / p) for p in banks}, 'accesses': sorted(set(accesses))})


def assess(rankings, grades):
    from scripts.improvement_cycle2 import evaluate
    result = evaluate(rankings, grades)
    comparisons = [('V2_DensePool', 'Dense'), ('V2_DensePool', 'V1_DensePool'),
                   ('V2_PerspectivePool', 'V2_DensePool'), ('V2_PerspectivePool', 'V2_TokenPool'),
                   ('V2_PerspectivePool', 'V1_PerspectivePool')]
    if any(r['system'] == 'V2_SparsePool' for r in rankings):
        comparisons.append(('V2_PerspectivePool', 'V2_SparsePool'))
    result['comparisons'] = {}
    for method, baseline in comparisons:
        values = {}
        for metric in ('F1@5', 'nDCG@10'):
            differences = [r[method][metric] - r[baseline][metric] for r in result['per_query'].values() if r[method][metric] is not None]
            values[metric] = {'delta': mean(differences), 'interval95': interval(differences),
                             'improved': sum(v > 1e-12 for v in differences), 'harmed': sum(v < -1e-12 for v in differences)}
        result['comparisons'][method + ':' + baseline] = values
    return result


def evaluate():
    frozen()
    from scripts.improvement_cycle2 import label_sets
    from scripts.ai_pilot_evaluate import assemble_votes
    pred20, pred40 = load('dev20-predictions.json'), load('reuse40-predictions.json')
    for scope, pred in [('dev20', pred20), ('reuse40', pred40)]:
        assert pred['input_sha256'] == sha(OUT / (scope + '-inputs.json'))
        assert pred['freeze_sha256'] == sha(OUT / 'freeze.json')
    dev = {}
    for name, grades in label_sets().items():
        dev[name] = assess(pred20['rankings'], grades)
        print('dev20', name, {s: round(v['F1@5']['mean'], 6) for s, v in dev[name]['summary'].items()}, flush=True)
    votes, _ = assemble_votes()
    labels = {}
    for provider, records in votes.items():
        grades = {}
        for (q, c), r in records.items():
            assert r['status'] == 'JUDGED' and r['grade'] is not None
            grades.setdefault(q, {})[c] = r['grade']
        labels[provider] = grades
    common = sorted(set.intersection(*[{q for q, g in grades.items() if any(v >= 2 for v in g.values())} for grades in labels.values()]))
    reuse, matched = {}, {}
    for provider, grades in labels.items():
        reuse[provider] = assess(pred40['rankings'], grades)
        matched[provider] = assess([r for r in pred40['rankings'] if r['query_id'] in common], {q: grades[q] for q in common})
        print('reuse40', provider, {s: round(v['F1@5']['mean'], 6) for s, v in reuse[provider]['summary'].items()}, flush=True)
    write('evaluation.json', {'dev20': dev, 'reuse40': reuse, 'common40': matched, 'common_questions': common,
        'prediction_sha256': {s: sha(OUT / (s + '-predictions.json')) for s in ('dev20', 'reuse40')},
        'paid_calls': 0, 'new_training': False, 'labels_changed': False, 'independent_test': False,
        'human_gold': False, 'test15_read': False, 'state': 'ALL_THREE_REQUESTED_STEPS_COMPLETE',
        'limits': ['Parser contracts are synthetic and assistant-authored', 'Both datasets previously inspected',
                   'Fixed weights isolate input changes, not newly trained scorer', 'Common-positive is same queries, not agreed case labels',
                   'Bootstrap not selection/multiplicity adjusted']})
    print('EVALUATION_COMPLETE', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['gate', 'infer', 'evaluate'])
    globals()[parser.parse_args().phase]()
