"""Stage six: freeze, one local ablation, existing-Silver evaluation, exact replay."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
import sys
import zipfile

import numpy as np

from ax_research.pilot_case_recommender import allocate, recommend_cases
from ax_research.pilot_perspective_selector import select_perspectives
from ax_research.pilot_catalog_evaluation import SYSTEMS, assess, metrics
from scripts.improvement_cycle import ROOT, read
from scripts.pilot_case_recommendation import inputs, LocalTaskScorer, PROFILES, REGISTRY, BANKS
from scripts.pilot_perspective_selection import CATALOG, RULES
from scripts.task_alignment_20261109 import sha

OUT = ROOT / 'docs/pilot-catalog-comparison-20261109'
DEV_INPUT = 'docs/task-alignment-20261109-inputs.json'
REUSE_INPUT = 'docs/transfer40-work-aligned-20261109/inputs.json'
STAGE5 = 'docs/pilot-case-recommendation-20261109-v1_2'
PILOT = 'docs/independent-validation-20261108/ai_pilot'
LABEL20 = {'original': 'docs/validation-new20-20261107/measured/labels_new20.json',
           'working_transfer': 'docs/ax-transfer-relevance-20261108/02_working_transfer_qrels_2240.json',
           'partial_review_464': 'docs/autonomous-improvement-20261108/19_independent_adjudication_and_stop_decision.json'}
SOURCES = [CATALOG, RULES, PROFILES, REGISTRY, DEV_INPUT, REUSE_INPUT,
    'src/ax_research/pilot_perspective_selector.py', 'src/ax_research/pilot_case_recommender.py',
    'src/ax_research/pilot_catalog_evaluation.py', 'scripts/pilot_case_recommendation.py',
    'scripts/pilot_catalog_comparison_20261109.py', 'tests/test_pilot_catalog_evaluation.py',
    'docs/pilot-catalog-comparison-20261109-protocol.md', STAGE5 + '/freeze.json',
    'docs/task-alignment-reference-20261109/config.json']


def write(name, value):
    with (OUT / name).open('x', encoding='utf-8') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def question_inputs():
    result = {}
    for scope, path in [('dev20', DEV_INPUT), ('reuse40', REUSE_INPUT)]:
        raw = read(path)
        for q, partition in sorted(raw['partitions'].items()):
            row = raw['inputs'][q]
            dense = row['dense'] if scope == 'dev20' else row['dense_order']
            assert len(dense) == len(set(dense)) == 112
            result[q] = {'scope': scope, 'text': partition['source_text'], 'dense112': dense}
    assert len(result) == 60
    return result


def frozen():
    freeze = load('freeze.json')
    assert all(sha(ROOT / p) == h for p, h in freeze['source_sha256'].items())
    assert all(sha(ROOT / p) == h for p, h in freeze['bank_sha256'].items())
    assert sha(OUT / 'questions.json') == freeze['questions_sha256']
    assert sha(OUT / 'source-snapshot.zip') == freeze['snapshot_sha256']
    return freeze


def freeze():
    if OUT.exists():
        raise FileExistsError(OUT)
    prior = read(STAGE5 + '/freeze.json')
    assert all(sha(ROOT / p) == h for p, h in prior['source_sha256'].items())
    questions = question_inputs()
    OUT.mkdir()
    write('questions.json', questions)
    with zipfile.ZipFile(OUT / 'source-snapshot.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in SOURCES:
            archive.write(ROOT / path, arcname=path)
    write('freeze.json', {'state': 'FIXED_BEFORE_PREDICTIONS_AND_NEW_LABEL_EVALUATION',
        'created_utc': datetime.now(timezone.utc).isoformat(),
        'source_sha256': {p: sha(ROOT / p) for p in SOURCES},
        'bank_sha256': {p: sha(ROOT / p) for p in BANKS + [STAGE5 + '/vectors.npz']},
        'questions_sha256': sha(OUT / 'questions.json'), 'snapshot_sha256': sha(OUT / 'source-snapshot.zip'),
        'questions': 60, 'cases': 17, 'candidate_budget': 20, 'output_budget': 5,
        'systems': list(SYSTEMS), 'seed': 20261109, 'bootstrap_resamples': 10000,
        'prior_development_exposure': True, 'new_labels': False, 'paid_calls': 0,
        'new_training': False, 'independent_final_test': False, 'test15_read': False})
    print('FROZEN_60_QUERIES_17_CASES', flush=True)


def branch_texts(question, selection):
    return {s['id']: '\n'.join(dict.fromkeys(e['clause_quote'] for e in s['evidence'] if e['kind'] == 'work')) or question
            for s in selection['selected']}


def no_condition_views(question, selection, catalog, scorer):
    cards = {c['id']: c for c in catalog['cards']}
    texts = branch_texts(question, selection)
    routes = {}
    for s in selection['selected']:
        ids = sorted(l['case_id'] for l in cards[s['id']]['links'] if l['status'] == 'SUPPORTED_FOR_PILOT')
        scores = scorer(s['id'], texts[s['id']], ids)
        routes[s['id']] = sorted([{'case_id': c, 'perspective_id': s['id'],
            'relationship': 'DIRECT_WORK_TYPE_CANDIDATE', 'semantic_task_cosine': scores[c]} for c in ids],
            key=lambda r: (-r['semantic_task_cosine'], r['case_id']))
    candidates = [r['case_id'] for r in allocate(routes, 20)]
    ranking = [r['case_id'] for r in allocate(routes, 5)]
    return {'ranking': ranking, 'candidates': candidates}


def predict_one(question, dense112, corpus, catalog, rules, profiles, registry, scorer):
    selected = select_perspectives(question, catalog, rules)
    scores = scorer('NO_PERSPECTIVE', question, corpus)
    task_rank = sorted(corpus, key=lambda c: (-scores[c], c))
    dense_rank = [c for c in dense112 if c in corpus]
    detail = recommend_cases(question, catalog, rules, profiles, registry, scorer)
    candidates = [r['case_id'] for r in allocate(detail['branches'], 20)]
    systems = {'A_Dense17': {'ranking': dense_rank[:5], 'candidates': dense_rank[:20]},
        'B_Task17': {'ranking': task_rank[:5], 'candidates': task_rank[:20], 'scores': scores},
        'C_Catalog17': {'ranking': [r['case_id'] for r in detail['recommendations']], 'candidates': candidates},
        'D_ViewsNoConditions17': no_condition_views(question, selected, catalog, scorer)}
    for value in systems.values():
        assert len(value['ranking']) <= 5 and len(value['candidates']) <= 20
        assert set(value['ranking']) <= set(value['candidates']) <= set(corpus)
        assert len(value['ranking']) == len(set(value['ranking']))
    return {'systems': systems, 'selected': [s['id'] for s in selected['selected']],
        'selector_state': selected['state'], 'catalog_state': detail['state'],
        'dense112_context': {'ranking': dense112[:5], 'candidates': dense112[:20]}}, detail


def infer():
    frozen()
    accesses = []
    def audit(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)):
            path = str(args[0]).replace('\\', '/').lower()
            if any(s in path for s in ('blind_review', '/qrels', 'labels_new20', 'ai_consensus.json',
                    '.ax-heldout', 'heldout-final-resume', '02_working_transfer', '19_independent_adjudication')):
                raise RuntimeError('No relevance or final-test content during inference')
            if path.endswith(('.json', '.jsonl', '.npz')):
                accesses.append(str(args[0]))
    sys.addaudithook(audit)
    catalog, rules, profiles, registry = inputs()
    corpus = sorted(profiles['cases'])
    questions = load('questions.json')
    scorer = LocalTaskScorer(registry)
    with np.load(ROOT / STAGE5 / 'vectors.npz', allow_pickle=False) as archive:
        scorer.bank.update(zip(archive['texts'].tolist(), archive['vectors']))
    texts = {registry[c]['task'] for c in corpus}
    for row in questions.values():
        texts.add(row['text'])
        texts.update(branch_texts(row['text'], select_perspectives(row['text'], catalog, rules)).values())
    print('LOCAL_ONLY_MISSING_STRINGS', len(texts - set(scorer.bank)), flush=True)
    scorer.warm(texts)
    predictions, details = {}, {}
    for q, row in questions.items():
        predictions[q], details[q] = predict_one(row['text'], row['dense112'], corpus, catalog, rules, profiles, registry, scorer)
        predictions[q]['scope'] = row['scope']
    selected = sorted(texts)
    np.savez_compressed(OUT / 'vectors.npz', texts=np.array(selected), vectors=np.array([scorer.bank[t] for t in selected], dtype=np.float32))
    write('predictions.json', {'questions': predictions, 'corpus': corpus,
        'freeze_sha256': sha(OUT / 'freeze.json'), 'vectors_sha256': sha(OUT / 'vectors.npz'),
        'paid_calls': 0, 'new_training': False, 'label_contents_read': False, 'test15_read': False})
    write('query-case-evidence.json', details)
    write('inference-audit.json', {'accessed_data_paths': sorted(set(accesses)),
        'new_vectors': len(scorer.new_vectors), 'questions': len(predictions),
        'selected_perspective_counts': dict(Counter(len(p['selected']) for p in predictions.values())),
        'labels_blocked_during_inference': True, 'paid_calls': 0, 'test15_read': False})
    print('PREDICTIONS_SAVED_BEFORE_LABEL_EVALUATION', len(predictions), flush=True)


def load_labels():
    labels, paths = {}, []
    for name in ('original', 'working_transfer'):
        path = LABEL20[name]
        raw = read(path)
        rows = raw.get('records', raw.get('ratings'))
        labels[name] = {}
        for row in rows:
            target = labels[name].setdefault(row['query_id'], {})
            assert row['case_id'] not in target
            target[row['case_id']] = row['grade']
        paths.append(path)
    partial = {q: dict(g) for q, g in labels['working_transfer'].items()}
    raw = read(LABEL20['partial_review_464'])
    assert len(raw['rows']) == 464
    for row in raw['rows']:
        partial[row['query_id']][row['case_id']] = row['conservative_grade']
    labels['partial_review_464'] = partial
    paths.append(LABEL20['partial_review_464'])
    for provider in ('claude', 'gemini'):
        grades = {}
        for i in range(1, 41):
            candidates = [f'{PILOT}/{folder}/{provider}_IVQ{i:03d}_validated.json'
                for folder in ('blind_review_v2', 'blind_review_429_recovery')]
            present = [p for p in candidates if (ROOT / p).exists()]
            assert len(present) == 1
            data = read(present[0])
            assert not data['parse_error'] and len(data['records']) == 112
            for row in data['records']:
                assert row['status'] == 'JUDGED' and row['grade'] is not None
                target = grades.setdefault(row['query_id'], {})
                assert row['case_id'] not in target
                target[row['case_id']] = row['grade']
            paths.append(present[0])
        labels[provider] = grades
    for name, grades in labels.items():
        assert len(grades) == (40 if name in ('claude', 'gemini') else 20)
        assert all(len(g) == 112 and all(isinstance(v, int) and 0 <= v <= 4 for v in g.values()) for g in grades.values())
    return labels, paths


def condition_diagnostic(predictions, details, profiles):
    """Metadata-consistency only, not an independent factual correctness metric."""
    output = {}
    for q, p in predictions.items():
        detail = details[q]
        if len(detail['perspective_selection']['selected']) > 1:
            output[q] = {'assessable': False, 'reason': 'Multiple selected works: do not propagate global conditions'}
            continue
        req = next(iter(detail['requirements_by_perspective'].values()), detail['requirements'])
        if not req['inputs'] and not req['read_only_required']:
            continue
        systems = {}
        for name, values in p['systems'].items():
            unsupported = []
            for c in values['ranking']:
                missing = sorted(set(req['inputs']) - set(profiles['cases'][c]['input_conditions']))
                if req['read_only_required']:
                    missing.append('read_only_not_certified')
                if missing:
                    unsupported.append({'case_id': c, 'unconfirmed_conditions': missing})
            systems[name] = {'emitted': len(values['ranking']), 'metadata_unconfirmed': unsupported}
        output[q] = {'assessable': True, 'requirements': req, 'systems': systems}
    return {'independent_gold': False, 'same_metadata_as_method': True, 'queries': output}


def compute_evaluation(predictions, labels, details, profiles, registry):
    corpus = sorted(profiles['cases'])
    results, coverage, global_results, context = {}, {}, {}, {}
    for name, grades in labels.items():
        subset = {q: p for q, p in predictions.items() if q in grades}
        results[name] = assess(subset, grades, corpus)
        global_results[name] = assess(subset, grades, sorted(registry))
        per_query = {}
        for q, g in grades.items():
            all_pos = {c for c, v in g.items() if v >= 2}
            inside = all_pos & set(corpus)
            per_query[q] = {'all112_positive': len(all_pos), 'inside17_positive': len(inside),
                'positive_mass_inside17': len(inside) / len(all_pos) if all_pos else None,
                'relevant_cases_excluded_by_pilot': sorted(all_pos - set(corpus))}
            row = subset[q]['dense112_context']
            context.setdefault(name, {})[q] = metrics(row['ranking'], row['candidates'], g)
        all_total = sum(r['all112_positive'] for r in per_query.values())
        inside_total = sum(r['inside17_positive'] for r in per_query.values())
        coverage[name] = {'queries': len(grades), 'positive_queries_all112': sum(r['all112_positive'] > 0 for r in per_query.values()),
            'positive_queries_inside17': sum(r['inside17_positive'] > 0 for r in per_query.values()),
            'positive_pairs_all112': all_total, 'positive_pairs_inside17': inside_total,
            'positive_pair_retention': inside_total / all_total if all_total else None,
            'per_query': per_query}
    common = sorted(q for q in labels['claude'] if all(any(g >= 2 for c, g in labels[p][q].items() if c in corpus) for p in ('claude', 'gemini')))
    matched = {p: assess({q: predictions[q] for q in common}, {q: labels[p][q] for q in common}, corpus) for p in ('claude', 'gemini')}
    sensitivity = {}
    for name in ('positive_intersection', 'positive_union'):
        grades = {q: {c: (2 if (all if name.endswith('intersection') else any)(labels[p][q][c] >= 2 for p in ('claude', 'gemini')) else 0)
                     for c in registry} for q in labels['claude']}
        sensitivity[name] = assess({q: predictions[q] for q in grades}, grades, corpus)
    selection = {scope: dict(Counter(p['selector_state'] for p in predictions.values() if p['scope'] == scope)) for scope in ('dev20', 'reuse40')}
    return {'state': 'FIXED_17_CASE_DEVELOPMENT_COMPARISON_COMPLETE', 'results_inside17': results,
        'results_all112_denominator': global_results, 'catalog_coverage': coverage,
        'dense112_context_only': context, 'common_positive_inside17_questions': common,
        'matched_provider_results': matched, 'provider_binary_sensitivity': sensitivity,
        'selector_states': selection, 'condition_diagnostic': condition_diagnostic(predictions, details, profiles),
        'human_gold': False, 'independent_final_test': False, 'test15_read': False,
        'paid_calls': 0, 'new_training': False, 'labels_changed': False,
        'limits': ['Previously inspected queries and assistant-curated pilot cases',
            'AI Silver disagreement retained; intersection/union are sensitivity cases, not truth',
            'Condition diagnostics reuse method metadata and are not independent accuracy',
            'Bootstrap correction within label set only, not development or all-label-set selection correction',
            '17-case restricted corpus; no full112 or paper-final superiority claim']}


def evaluate():
    frozen()
    raw = load('predictions.json')
    assert raw['freeze_sha256'] == sha(OUT / 'freeze.json')
    assert raw['vectors_sha256'] == sha(OUT / 'vectors.npz')
    labels, paths = load_labels()
    catalog, rules, profiles, registry = inputs()
    output = compute_evaluation(raw['questions'], labels, load('query-case-evidence.json'), profiles, registry)
    output['prediction_sha256'] = sha(OUT / 'predictions.json')
    output['evidence_sha256'] = sha(OUT / 'query-case-evidence.json')
    output['label_sha256'] = {p: sha(ROOT / p) for p in paths}
    write('evaluation.json', output)
    for name, result in output['results_inside17'].items():
        print(name, 'positive_questions', result['positive_questions'],
              {s: result['summary'][s]['F1@5']['mean'] for s in SYSTEMS}, flush=True)


def verify():
    frozen()
    raw, questions = load('predictions.json'), load('questions.json')
    evaluation = load('evaluation.json')
    assert evaluation['prediction_sha256'] == sha(OUT / 'predictions.json')
    assert evaluation['evidence_sha256'] == sha(OUT / 'query-case-evidence.json')
    assert all(sha(ROOT / p) == h for p, h in evaluation['label_sha256'].items())
    assert raw['vectors_sha256'] == sha(OUT / 'vectors.npz')
    catalog, rules, profiles, registry = inputs()
    scorer = LocalTaskScorer(registry)
    # Only saved stage-six vectors are allowed for exact replay.
    with np.load(OUT / 'vectors.npz', allow_pickle=False) as archive:
        scorer.bank = dict(zip(archive['texts'].tolist(), archive['vectors']))
    def saved_scores(p, q, ids):
        return {c: float(np.clip(scorer.bank[q] @ scorer.bank[registry[c]['task']], -1, 1)) for c in ids}
    details = load('query-case-evidence.json')
    for q, row in questions.items():
        replay, detail = predict_one(row['text'], row['dense112'], raw['corpus'], catalog, rules, profiles, registry, saved_scores)
        replay['scope'] = row['scope']
        assert replay == raw['questions'][q], q
        assert detail == details[q], q
    labels, _ = load_labels()
    recomputed = compute_evaluation(raw['questions'], labels, details, profiles, registry)
    assert all(recomputed[k] == evaluation[k] for k in recomputed)
    result = {'state': 'PASS_FROZEN_SOURCES_60_PREDICTIONS_AND_METRICS_REPLAY',
        'replayed_questions': 60, 'systems_per_question': 4, 'frozen_stage5_unchanged': True,
        'label_files_unchanged': len(evaluation['label_sha256']), 'new_training': False,
        'paid_calls': 0, 'test15_read': False, 'independent_gold': False,
        'evaluation_sha256': sha(OUT / 'evaluation.json')}
    (OUT / 'verification.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['freeze', 'infer', 'evaluate', 'verify'])
    globals()[parser.parse_args().phase]()
