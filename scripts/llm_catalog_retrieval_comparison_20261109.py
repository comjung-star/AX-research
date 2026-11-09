"""One frozen 17-case comparison: actual LLM choice, unchanged retrieval, Silver replay."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
import sys
import urllib.error
import urllib.request
import zipfile

import numpy as np

from ax_research.llm_catalog_selector import request_body, parse_response
from ax_research.llm_catalog_retrieval import adapt_selection, recommend_llm
from ax_research.pilot_case_recommender import recommend_cases, allocate
from ax_research.pilot_catalog_evaluation import metrics, summarize, paired_interval
from scripts.pilot_case_recommendation import inputs, LocalTaskScorer, BANKS, PROFILES, REGISTRY
from scripts.pilot_perspective_selection import CATALOG, RULES
from scripts.pilot_catalog_comparison_20261109 import load_labels
from scripts.improvement_cycle import ROOT, read
from scripts.task_alignment_20261109 import sha

OUT = ROOT / 'docs/llm-catalog-retrieval-comparison-20261109'
PRIOR = 'docs/pilot-catalog-comparison-20261109'
SELECTOR = 'docs/llm-catalog-selector-20261109'
CONFIG = 'configs/llm_catalog_selector_20261109.json'
REGRESSION_IDS = ('IVQ010', 'IVQ015', 'IVQ020', 'IVQ029')
SYSTEMS = ('A_Dense17', 'B_Task17', 'C_Catalog17', 'E_LLMCatalog17')
CONTRASTS = tuple(('E_LLMCatalog17', b) for b in SYSTEMS[:-1])
SOURCES = [CONFIG, CATALOG, RULES, PROFILES, REGISTRY,
    'src/ax_research/llm_catalog_selector.py', 'src/ax_research/llm_catalog_retrieval.py',
    'src/ax_research/pilot_perspective_selector.py', 'src/ax_research/pilot_case_recommender.py',
    'src/ax_research/pilot_catalog_evaluation.py', 'scripts/pilot_case_recommendation.py',
    'scripts/pilot_catalog_comparison_20261109.py', 'scripts/llm_catalog_retrieval_comparison_20261109.py',
    'tests/test_llm_catalog_retrieval.py', 'docs/llm-catalog-retrieval-comparison-20261109-protocol.md',
    'docs/task-alignment-reference-20261109/config.json', PRIOR + '/questions.json', PRIOR + '/predictions.json',
    PRIOR + '/query-case-evidence.json', SELECTOR + '/final-freeze.json', SELECTOR + '/requests.json',
    SELECTOR + '/normalized-selections.json', SELECTOR + '/questions-and-development-expectations.json']


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    for name in ('ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY'):
        secret = os.environ.get(name)
        if secret and secret in text:
            raise ValueError('Refusing to write credentials')
    with path.open('x', encoding='utf-8') as stream:
        stream.write(text)


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def frozen():
    x = load('freeze.json')
    assert all(sha(ROOT / p) == h for p, h in x['source_sha256'].items())
    assert all(sha(ROOT / p) == h for p, h in x['bank_sha256'].items())
    assert all(sha(OUT / p) == h for p, h in x['artifact_sha256'].items())
    return x


def prepare():
    if OUT.exists():
        raise FileExistsError('Existing comparison must be preserved')
    prior_freeze = read(PRIOR + '/freeze.json')
    llm_freeze = read(SELECTOR + '/final-freeze.json')
    for f in (prior_freeze, llm_freeze):
        assert all(sha(ROOT / p) == h for p, h in f['source_sha256'].items())
    assert llm_freeze['normalized_sha256'] == sha(ROOT / SELECTOR / 'normalized-selections.json')
    config = read(CONFIG)
    catalog, rules, profiles, registry = inputs()
    questions = read(PRIOR + '/questions.json')
    previous_requests = read(SELECTOR + '/requests.json')
    previous_normalized = read(SELECTOR + '/normalized-selections.json')
    requests, reused, reservations = {}, {}, {}
    for q, row in questions.items():
        body = request_body(row['text'], config, catalog['cards'])
        if q in REGRESSION_IDS:
            key = 'R_' + q
            assert body == previous_requests[key]
            assert previous_normalized[key]['question'] == row['text']
            reused[q] = {'source_key': key, 'normalized': previous_normalized[key],
                'source_response': SELECTOR + '/calls/' + key + '-response.json'}
        else:
            requests[q] = body
            upper = len(json.dumps(body, ensure_ascii=False).encode('utf-8')) + 8192
            reservations[q] = {'input_tokens_upper': upper, 'output_token_cap': config['max_tokens'],
                'reserved_upper_usd': (upper * config['input_rate_per_million'] + config['max_tokens'] * config['output_rate_per_million']) / 1e6}
    assert len(requests) == 56 and len(reused) == 4
    reserved = sum(r['reserved_upper_usd'] for r in reservations.values())
    assert reserved <= 5
    assert os.environ.get('ANTHROPIC_API_KEY'), 'Existing Claude key unavailable'
    OUT.mkdir()
    (OUT / 'calls').mkdir()
    save(OUT / 'questions.json', questions)
    save(OUT / 'requests.json', requests)
    save(OUT / 'reused-selections.json', reused)
    save(OUT / 'reservation.json', {'reservations': reservations, 'reserved_upper_usd': reserved,
        'budget_usd': 5, 'new_call_cap': 56, 'reused_calls': 4, 'retries': 0,
        'pricing_source': config['pricing_source'], 'rates_per_million': [2, 10]})
    paths = SOURCES + [r['source_response'] for r in reused.values()]
    with zipfile.ZipFile(OUT / 'source-snapshot.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for p in paths:
            archive.write(ROOT / p, arcname=p)
    save(OUT / 'freeze.json', {'state': 'FROZEN_BEFORE_NEW_LLM_CALLS_AND_RETRIEVAL', 'created_utc': now(),
        'source_sha256': {p: sha(ROOT / p) for p in paths},
        'bank_sha256': {p: sha(ROOT / p) for p in BANKS + [PRIOR + '/vectors.npz']},
        'artifact_sha256': {p: sha(OUT / p) for p in ['questions.json', 'requests.json', 'reused-selections.json', 'reservation.json', 'source-snapshot.zip']},
        'model': config['model'], 'effort': config['effort'], 'questions': 60, 'cases': 17,
        'systems': list(SYSTEMS), 'contrasts': list(CONTRASTS), 'new_call_cap': 56, 'reused_calls': 4,
        'reserved_upper_usd': reserved, 'new_training': False, 'retrieval_labels_sent': False,
        'prior_development_exposure': True, 'test15_read': False})
    print(json.dumps({'state': 'FROZEN_READY', 'new_calls': 56, 'reused_calls': 4, 'reserved_upper_usd': reserved}), flush=True)


def one_call(q, body, reservation, config):
    path = OUT / 'calls'
    save(path / (q + '-attempt.json'), {'state': 'RESERVED_BEFORE_SEND_NO_RETRY', 'started_utc': now(),
        'model': config['model'], 'reserved_upper_usd': reservation['reserved_upper_usd']})
    request = urllib.request.Request('https://api.anthropic.com/v1/messages', json.dumps(body).encode('utf-8'),
        headers={'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        save(path / (q + '-failure.json'), {'state': 'HTTP_FAILURE_NO_RETRY', 'status': error.code, 'reservation_retained': True})
        return {'id': q, 'state': 'HTTP_FAILURE'}
    except Exception:
        save(path / (q + '-failure.json'), {'state': 'UNKNOWN_DELIVERY_NO_RETRY', 'reservation_retained': True})
        return {'id': q, 'state': 'UNKNOWN_DELIVERY'}
    save(path / (q + '-response.json'), data)
    usage = data.get('usage', {})
    cost = (usage.get('input_tokens', 0) * config['input_rate_per_million'] + usage.get('output_tokens', 0) * config['output_rate_per_million']) / 1e6
    save(path / (q + '-receipt.json'), {'response_id': data.get('id'), 'model': data.get('model'), 'usage': usage,
        'estimated_usd': cost, 'stop_reason': data.get('stop_reason'), 'finished_utc': now()})
    try:
        question = json.loads(body['messages'][0]['content'])['question']
        parsed = parse_response(question, data)
        save(path / (q + '-normalized.json'), parsed)
        return {'id': q, 'state': 'VALID', 'selected_ids': parsed['selected_ids'], 'estimated_usd': cost}
    except Exception as error:
        save(path / (q + '-parse-failure.json'), {'state': 'OUTPUT_RETAINED_NO_RETRY', 'error_type': type(error).__name__, 'error': str(error)[:240]})
        return {'id': q, 'state': 'OUTPUT_VALIDATION_FAILED', 'estimated_usd': cost}


def select():
    frozen()
    if (OUT / 'selection-start.json').exists() or list((OUT / 'calls').glob('*-attempt.json')):
        raise FileExistsError('Existing attempts cannot be sent again')
    config = read(CONFIG)
    requests, reserved = load('requests.json'), load('reservation.json')
    save(OUT / 'selection-start.json', {'started_utc': now(), 'planned_new_calls': len(requests),
        'reused_calls': 4, 'reserved_upper_usd': reserved['reserved_upper_usd'], 'workers': 3, 'retries': 0})
    outcomes = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(one_call, q, body, reserved['reservations'][q], config) for q, body in requests.items()]
        for future in as_completed(futures):
            result = future.result()
            outcomes.append(result)
            print(json.dumps(result, ensure_ascii=False), flush=True)
    normalized = {q: r['normalized'] for q, r in load('reused-selections.json').items()}
    for q in requests:
        path = OUT / 'calls' / (q + '-normalized.json')
        if path.exists():
            normalized[q] = json.loads(path.read_text(encoding='utf-8'))
    save(OUT / 'selections.json', normalized)
    save(OUT / 'selection-run.json', {'state': 'REAL_LLM_SELECTION_COMPLETE', 'finished_utc': now(),
        'outcomes': sorted(outcomes, key=lambda r: r['id']), 'new_attempts': len(outcomes), 'reused_selections': 4,
        'valid_selections': len(normalized), 'estimated_new_usage_usd': sum(r.get('estimated_usd', 0) for r in outcomes),
        'reserved_upper_usd': reserved['reserved_upper_usd'], 'retries': 0, 'prompt_modified': False})
    print('SELECTIONS_SAVED', len(normalized), flush=True)


def failure_selection(question):
    return {'question': question, 'version': 'llm-catalog-selector-v1-20261109', 'state': 'REVIEW_NEEDED',
        'selected_ids': [], 'pending_ids': ['P01', 'P02', 'P03', 'P04'], 'decisions': [
            {'id': p, 'status': 'PENDING', 'rationale': 'LLM 응답 전달 또는 구조 검증 실패',
             'missing_information': ['유효한 관점 선택 응답'], 'evidence': []} for p in ('P01', 'P02', 'P03', 'P04')],
        'unsupported_work': [], 'constraints': [], 'technical_failure': True}


def ranking(detail):
    return {'ranking': [r['case_id'] for r in detail['recommendations']],
        'candidates': [r['case_id'] for r in allocate(detail['branches'], 20)]}


def infer():
    frozen()
    accesses = []
    def audit(event, args):
        if event == 'open' and isinstance(args[0], (str, bytes)):
            p = str(args[0]).replace('\\', '/').lower()
            if any(s in p for s in ('blind_review', '/qrels', 'labels_new20', 'ai_consensus.json',
                '.ax-heldout', 'heldout-final-resume', '02_working_transfer', '19_independent_adjudication')):
                raise RuntimeError('No relevance/final-test content during inference')
            if p.endswith(('.json', '.jsonl', '.npz')):
                accesses.append(str(args[0]))
    sys.addaudithook(audit)
    catalog, rules, profiles, registry = inputs()
    questions, selected = load('questions.json'), load('selections.json')
    old = read(PRIOR + '/predictions.json')['questions']
    old_details = read(PRIOR + '/query-case-evidence.json')
    scorer = LocalTaskScorer(registry)
    with np.load(ROOT / PRIOR / 'vectors.npz', allow_pickle=False) as archive:
        scorer.bank.update(zip(archive['texts'].tolist(), archive['vectors']))
    texts = set()
    for detail in old_details.values():
        for s in detail['perspective_selection']['selected']:
            texts.add('\n'.join(dict.fromkeys(e['clause_quote'] for e in s['evidence'] if e['kind'] == 'work')) or detail['question'])
    adapted = {}
    for q, row in questions.items():
        a = adapt_selection(row['text'], selected.get(q, failure_selection(row['text'])), catalog)
        adapted[q] = a
        for s in a['selected']:
            texts.add('\n'.join(dict.fromkeys(e['clause_quote'] for e in s['evidence'] if e['kind'] == 'work')) or row['text'])
        texts.add(row['text'])
    texts.update(registry[c]['task'] for c in profiles['cases'])
    # Local integration examples only; no retrieval-label evaluation of these.
    development = read(SELECTOR + '/normalized-selections.json')
    for d in development.values():
        a = adapt_selection(d['question'], d, catalog)
        texts.update('\n'.join(dict.fromkeys(e['clause_quote'] for e in s['evidence'] if e['kind'] == 'work')) or d['question'] for s in a['selected'])
    print('LOCAL_ONLY_NEW_STRINGS', len(texts - set(scorer.bank)), flush=True)
    scorer.warm(texts)
    results, details, technical = {}, {}, []
    for q, row in questions.items():
        text = row['text']
        rule = recommend_cases(text, catalog, rules, profiles, registry, scorer)
        assert rule == old_details[q], 'Rule core changed: ' + q
        assert ranking(rule) == old[q]['systems']['C_Catalog17']
        llm = recommend_llm(text, selected.get(q, failure_selection(text)), catalog, rules, profiles, registry, scorer)
        details[q] = llm
        systems = {s: old[q]['systems'][s] for s in SYSTEMS[:-1]}
        systems['E_LLMCatalog17'] = ranking(llm)
        results[q] = {'scope': row['scope'], 'systems': systems, 'llm_selected': selected[q]['selected_ids'] if q in selected else [],
            'adapted_selected': [s['id'] for s in adapted[q]['selected']], 'llm_state': selected[q]['state'] if q in selected else 'TECHNICAL_FAILURE',
            'adapter_state': adapted[q]['state'], 'catalog_state': llm['state'], 'adapter_problems': adapted[q]['adapter_review_required'],
            'previous_selector_development_query': q in REGRESSION_IDS}
        if q not in selected:
            technical.append(q)
        for value in systems.values():
            assert len(value['ranking']) <= 5 and len(value['candidates']) <= 20
            assert set(value['ranking']) <= set(value['candidates']) <= set(profiles['cases'])
    examples = {q: recommend_llm(d['question'], d, catalog, rules, profiles, registry, scorer) for q, d in development.items()}
    all_texts = sorted(texts)
    np.savez_compressed(OUT / 'vectors.npz', texts=np.array(all_texts), vectors=np.array([scorer.bank[t] for t in all_texts], dtype=np.float32))
    save(OUT / 'predictions.json', {'questions': results, 'corpus': sorted(profiles['cases']),
        'freeze_sha256': sha(OUT / 'freeze.json'), 'selections_sha256': sha(OUT / 'selections.json'),
        'vectors_sha256': sha(OUT / 'vectors.npz'), 'technical_failure_questions': technical,
        'labels_read_during_inference': False, 'test15_read': False, 'new_training': False})
    save(OUT / 'query-case-evidence.json', details)
    save(OUT / 'integration-examples.json', examples)
    save(OUT / 'inference-audit.json', {'opened_data_paths': sorted(set(accesses)), 'new_encoded_strings': len(scorer.new_vectors),
        'legacy_rule_details_exact_replayed': 60, 'legacy_A_B_C_rankings_unchanged': True, 'technical_failure_questions': technical,
        'adapter_review_questions': [q for q, r in results.items() if r['adapter_problems']], 'labels_blocked': True,
        'test15_read': False, 'paid_calls_in_this_local_phase': 0})
    print('ALL_60_RANKINGS_SAVED_BEFORE_LABEL_EVALUATION', flush=True)


def assess(predictions, grades, corpus):
    rows = {q: {s: metrics(r['systems'][s]['ranking'], r['systems'][s]['candidates'], {c: grades[q][c] for c in corpus})
                for s in SYSTEMS} for q, r in predictions.items()}
    contrasts = {m + ':' + b: {metric: paired_interval([r[m][metric] - r[b][metric] for r in rows.values() if r[m][metric] is not None])
                  for metric in ('F1@5', 'nDCG@5')} for m, b in CONTRASTS}
    return {'summary': summarize(rows, SYSTEMS), 'per_query': rows,
        'positive_questions': sum(any(v >= 2 for c, v in grades[q].items() if c in corpus) for q in predictions), 'contrasts': contrasts}


def compute_evaluation(predictions, labels, details, registry):
    corpus = read(PRIOR + '/predictions.json')['corpus']
    results, global_results, subgroups, coverage = {}, {}, {}, {}
    for name, grades in labels.items():
        chosen = {q: r for q, r in predictions.items() if q in grades}
        results[name] = assess(chosen, grades, corpus)
        global_results[name] = assess(chosen, grades, sorted(registry))
        all_pos = sum(v >= 2 for g in grades.values() for v in g.values())
        retained = sum(v >= 2 for g in grades.values() for c, v in g.items() if c in corpus)
        coverage[name] = {'positive_pairs_all112': all_pos, 'positive_pairs_inside17': retained,
            'positive_pair_retention': retained / all_pos if all_pos else None}
        if name in ('claude', 'gemini'):
            subgroups[name] = {}
            for title, ids in [('previous_selector_development4', REGRESSION_IDS),
                               ('remaining_previously_seen36', [q for q in grades if q not in REGRESSION_IDS])]:
                subset = {q: chosen[q] for q in ids}
                subgroups[name][title] = assess(subset, {q: grades[q] for q in ids}, corpus)
    common = sorted(q for q in labels['claude'] if all(any(v >= 2 for c, v in labels[p][q].items() if c in corpus) for p in ('claude', 'gemini')))
    matched = {p: assess({q: predictions[q] for q in common}, {q: labels[p][q] for q in common}, corpus) for p in ('claude', 'gemini')}
    sensitivity = {}
    for mode in ('intersection', 'union'):
        grades = {q: {c: 2 if (all if mode == 'intersection' else any)(labels[p][q][c] >= 2 for p in ('claude', 'gemini')) else 0
            for c in registry} for q in labels['claude']}
        sensitivity[mode] = assess({q: predictions[q] for q in grades}, grades, corpus)
    accounting = {}
    for name, grades in labels.items():
        group = {}
        for q, g in grades.items():
            pos = {c for c, v in g.items() if v >= 2} & set(corpus)
            candidate = set(predictions[q]['systems']['E_LLMCatalog17']['candidates'])
            final = set(predictions[q]['systems']['E_LLMCatalog17']['ranking'])
            chosen_ids = predictions[q]['adapted_selected']
            group[q] = {'positive_inside17': sorted(pos), 'missing_from_candidates': sorted(pos-candidate),
                'lost_by_no_selected_view': sorted(pos) if not chosen_ids else [],
                'lost_by_final5': sorted((pos & candidate)-final), 'selected_views': chosen_ids,
                'positive_hits_final': sorted(pos & final)}
        accounting[name] = group
    return {'state': 'FIXED_LLM_SELECTION_TO_RETRIEVAL_DEVELOPMENT_COMPARISON_COMPLETE',
        'results_inside17': results, 'results_all112_denominator': global_results,
        'matched_provider_results': matched, 'common_positive_inside17_questions': common,
        'selector_development_subgroups': subgroups, 'binary_sensitivity': sensitivity,
        'catalog_coverage': coverage, 'failure_accounting': accounting,
        'selection_counts': {scope: dict(Counter(len(r['adapted_selected']) for r in predictions.values() if r['scope'] == scope)) for scope in ('dev20', 'reuse40')},
        'human_gold': False, 'independent_final_test': False, 'test15_read': False,
        'new_training': False, 'labels_changed': False, 'scope_expanded_to112': False,
        'limits': ['Previously observed questions and small assistant-curated catalog',
            '4 LLM selector development questions reused and separately reported',
            'Old clause/condition parser retained; ambiguous mappings remain pending',
            'AI Silver disagreement and development selection bias remain',
            'Paired bootstrap not independent test or all-label-set multiplicity correction']}


def evaluate():
    frozen()
    raw = load('predictions.json')
    assert raw['vectors_sha256'] == sha(OUT / 'vectors.npz') and raw['selections_sha256'] == sha(OUT / 'selections.json')
    labels, label_paths = load_labels()
    registry = inputs()[3]
    result = compute_evaluation(raw['questions'], labels, load('query-case-evidence.json'), registry)
    result['prediction_sha256'] = sha(OUT / 'predictions.json')
    result['evidence_sha256'] = sha(OUT / 'query-case-evidence.json')
    result['label_sha256'] = {p: sha(ROOT / p) for p in label_paths}
    result['new_api_cost'] = load('selection-run.json')['estimated_new_usage_usd']
    save(OUT / 'evaluation.json', result)
    for name, r in result['results_inside17'].items():
        print(name, r['positive_questions'], {s: r['summary'][s]['F1@5']['mean'] for s in SYSTEMS}, flush=True)


def verify():
    frozen()
    raw, selected, questions = load('predictions.json'), load('selections.json'), load('questions.json')
    result = load('evaluation.json')
    assert raw['freeze_sha256'] == sha(OUT / 'freeze.json')
    assert raw['selections_sha256'] == sha(OUT / 'selections.json') and raw['vectors_sha256'] == sha(OUT / 'vectors.npz')
    assert result['prediction_sha256'] == sha(OUT / 'predictions.json') and result['evidence_sha256'] == sha(OUT / 'query-case-evidence.json')
    assert all(sha(ROOT / p) == h for p, h in result['label_sha256'].items())
    bodies, reserved = load('requests.json'), load('reservation.json')
    config = read(CONFIG)
    cost, receipts, reused_count = 0, 0, 0
    for q, row in questions.items():
        body = request_body(row['text'], config, inputs()[0]['cards'])
        if q in bodies:
            assert body == bodies[q]
            path = OUT / 'calls' / (q + '-response.json')
        else:
            previous = load('reused-selections.json')[q]
            path = ROOT / previous['source_response']
            reused_count += 1
        if path.exists():
            response = json.loads(path.read_text(encoding='utf-8'))
            try:
                parsed = parse_response(row['text'], response)
            except Exception:
                assert q not in selected
            else:
                assert parsed == selected[q]
        if q in bodies and (OUT / 'calls' / (q + '-receipt.json')).exists():
            receipt = json.loads((OUT / 'calls' / (q + '-receipt.json')).read_text(encoding='utf-8'))
            assert receipt['estimated_usd'] <= reserved['reservations'][q]['reserved_upper_usd']
            cost += receipt['estimated_usd']
            receipts += 1
    assert abs(cost - load('selection-run.json')['estimated_new_usage_usd']) < 1e-9
    catalog, rules, profiles, registry = inputs()
    with np.load(OUT / 'vectors.npz', allow_pickle=False) as z:
        bank = dict(zip(z['texts'].tolist(), z['vectors']))
    def scorer(p, text, ids):
        return {c: float(np.clip(bank[text] @ bank[registry[c]['task']], -1, 1)) for c in ids}
    details = load('query-case-evidence.json')
    old = read(PRIOR + '/predictions.json')['questions']
    for q, row in questions.items():
        llm = recommend_llm(row['text'], selected.get(q, failure_selection(row['text'])), catalog, rules, profiles, registry, scorer)
        assert llm == details[q] and ranking(llm) == raw['questions'][q]['systems']['E_LLMCatalog17']
        rule = recommend_cases(row['text'], catalog, rules, profiles, registry, scorer)
        assert ranking(rule) == old[q]['systems']['C_Catalog17']
        for s in SYSTEMS[:-1]:
            assert raw['questions'][q]['systems'][s] == old[q]['systems'][s]
    labels, _ = load_labels()
    recomputed = compute_evaluation(raw['questions'], labels, details, registry)
    assert all(recomputed[k] == result[k] for k in recomputed)
    report = {'state': 'PASS_SAVED_LLM_RESPONSES_60_RETRIEVALS_AND_METRICS_REPLAY',
        'new_receipts': receipts, 'reused_responses': reused_count, 'valid_llm_selections': len(selected),
        'retrieval_questions_replayed': 60, 'legacy_A_B_C_unchanged': True,
        'unchanged_label_files': len(result['label_sha256']), 'estimated_new_api_usd': cost,
        'reserved_upper_usd': reserved['reserved_upper_usd'], 'new_training': False,
        'prompt_changes_after_outputs': 0, 'test15_read': False, 'independent_gold': False,
        'evaluation_sha256': sha(OUT / 'evaluation.json')}
    (OUT / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'select', 'infer', 'evaluate', 'verify'])
    globals()[parser.parse_args().phase]()
