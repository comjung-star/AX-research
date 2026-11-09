"""Bounded real Claude selection pilot, without case retrieval or new judging."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import json
import os
import urllib.error
import urllib.request
import zipfile

from ax_research.llm_catalog_selector import request_body, parse_response
from scripts.improvement_cycle import ROOT, read
from scripts.task_alignment_20261109 import sha

CONFIG = 'configs/llm_catalog_selector_20261109.json'
DEVELOPMENT = 'configs/llm_catalog_selector_development_20261109.json'
OUT = ROOT / 'docs/llm-catalog-selector-20261109'
PRIOR_QUESTIONS = 'docs/pilot-catalog-comparison-20261109/questions.json'
SOURCES = [CONFIG, DEVELOPMENT, 'src/ax_research/llm_catalog_selector.py',
    'scripts/llm_catalog_selector_20261109.py', 'tests/test_llm_catalog_selector.py',
    'docs/llm-catalog-selector-20261109-protocol.md', PRIOR_QUESTIONS,
    'docs/pilot-case-recommendation-20261109-v1_2/freeze.json']


def now():
    return datetime.now(timezone.utc).isoformat()


def save(path, value):
    text = json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    for name in ('ANTHROPIC_API_KEY', 'GEMINI_API_KEY', 'OPENAI_API_KEY'):
        secret = os.environ.get(name)
        if secret and secret in text:
            raise ValueError('Credential must never be written to an artifact')
    with path.open('x', encoding='utf-8') as stream:
        stream.write(text)


def load(name):
    return json.loads((OUT / name).read_text(encoding='utf-8'))


def frozen():
    freeze = load('freeze.json')
    assert all(sha(ROOT / p) == h for p, h in freeze['source_sha256'].items())
    assert all(sha(OUT / p) == h for p, h in freeze['artifact_sha256'].items())
    return freeze


def develop_rows():
    development = read(DEVELOPMENT)
    previous = read(PRIOR_QUESTIONS)
    rows = [{**r, 'kind': 'SYNTHETIC_DEVELOPMENT', 'reverse_cards': False} for r in development['cases']]
    for r in development['regressions']:
        rows.append({**r, 'question': previous[r['source_query']]['text'], 'kind': 'PREVIOUSLY_SEEN_REGRESSION', 'reverse_cards': False})
    lookup = {r['id']: r for r in rows}
    for q in development['repeat_ids']:
        rows.append({**lookup[q], 'id': q + '_REVERSE', 'kind': 'ORDER_DIAGNOSTIC_REPEAT',
            'repeat_of': q, 'reverse_cards': True})
    assert len(rows) == 28 and len({r['id'] for r in rows}) == 28
    return rows


def prepare():
    if OUT.exists():
        raise FileExistsError('Existing run must be preserved')
    config = read(CONFIG)
    catalog = read(config['source_catalog'])
    assert catalog['version'] == config['source_catalog_version']
    prior = read('docs/pilot-case-recommendation-20261109-v1_2/freeze.json')
    assert all(sha(ROOT / p) == h for p, h in prior['source_sha256'].items())
    assert os.environ.get('ANTHROPIC_API_KEY'), 'Configured Claude key is unavailable'
    rows = develop_rows()
    bodies = {r['id']: request_body(r['question'], config, catalog['cards'], reverse=r['reverse_cards']) for r in rows}
    reservations = {}
    for q, body in bodies.items():
        input_upper = len(json.dumps(body, ensure_ascii=False).encode('utf-8')) + 8192
        reserved = (input_upper * config['input_rate_per_million'] + config['max_tokens'] * config['output_rate_per_million']) / 1e6
        reservations[q] = {'input_token_upper_by_bytes_plus_margin': input_upper, 'output_token_cap': config['max_tokens'], 'reserved_upper_usd': reserved}
    total = sum(v['reserved_upper_usd'] for v in reservations.values())
    assert len(bodies) <= config['max_calls'] and total <= config['budget_usd'], f'Reservation exceeds budget: {total:.4f}'
    OUT.mkdir()
    (OUT / 'calls').mkdir()
    save(OUT / 'questions-and-development-expectations.json', {'rows': rows, 'human_gold': False})
    save(OUT / 'requests.json', bodies)
    save(OUT / 'reservation.json', {'reservations': reservations, 'reserved_upper_usd': total, 'limit_usd': config['budget_usd'],
        'max_paid_calls': len(rows), 'retries': 0, 'pricing_source': config['pricing_source'], 'prepared_utc': now()})
    # Availability metadata only; this is not a billed Messages request.
    request = urllib.request.Request('https://api.anthropic.com/v1/models/' + config['model'], headers={
        'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01'})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            metadata = json.load(response)
    except urllib.error.HTTPError as error:
        save(OUT / 'preflight-failure.json', {'state': 'MODEL_AVAILABILITY_FAILED_NO_PAID_CALL', 'status': error.code})
        raise RuntimeError('Claude model availability check failed; HTTP ' + str(error.code)) from None
    except Exception:
        save(OUT / 'preflight-failure.json', {'state': 'MODEL_AVAILABILITY_UNCERTAIN_NO_PAID_CALL'})
        raise RuntimeError('Claude availability could not be confirmed; no paid call started') from None
    assert metadata.get('id') == config['model']
    save(OUT / 'model-metadata.json', metadata)
    source_paths = SOURCES + [config['source_catalog']]
    with zipfile.ZipFile(OUT / 'source-snapshot.zip', 'x', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in source_paths:
            archive.write(ROOT / path, arcname=path)
    save(OUT / 'freeze.json', {'state': 'FROZEN_BEFORE_FIRST_PAID_SELECTION_CALL', 'created_utc': now(),
        'source_sha256': {p: sha(ROOT / p) for p in source_paths},
        'artifact_sha256': {p: sha(OUT / p) for p in ['questions-and-development-expectations.json', 'requests.json',
            'reservation.json', 'model-metadata.json', 'source-snapshot.zip']},
        'max_paid_calls': len(rows), 'reserved_upper_usd': total, 'model': config['model'],
        'effort': config['effort'], 'fine_tuning': False, 'retrieval_performed': False,
        'retrieval_labels_sent': False, 'test15_read': False, 'prior_development_exposure': True})
    print(json.dumps({'state': 'READY_FROZEN_MODEL_AVAILABLE', 'model': config['model'], 'calls': len(rows),
        'reserved_upper_usd': total, 'paid_calls_so_far': 0}), flush=True)


def one_call(row, body, reservation, config):
    q = row['id']
    path = OUT / 'calls'
    save(path / (q + '-attempt.json'), {'state': 'RESERVED_BEFORE_SEND_NO_RETRY', 'started_utc': now(),
        'reserved_upper_usd': reservation['reserved_upper_usd'], 'model': config['model']})
    request = urllib.request.Request('https://api.anthropic.com/v1/messages', json.dumps(body).encode('utf-8'),
        headers={'x-api-key': os.environ['ANTHROPIC_API_KEY'], 'anthropic-version': '2023-06-01', 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            result = json.load(response)
    except urllib.error.HTTPError as error:
        save(path / (q + '-failure.json'), {'state': 'HTTP_FAILURE_NO_RETRY', 'status': error.code,
            'reservation_retained': True, 'finished_utc': now()})
        return {'id': q, 'state': 'HTTP_FAILURE', 'http_status': error.code}
    except Exception:
        save(path / (q + '-failure.json'), {'state': 'UNKNOWN_DELIVERY_NO_RETRY', 'reservation_retained': True, 'finished_utc': now()})
        return {'id': q, 'state': 'UNKNOWN_DELIVERY'}
    save(path / (q + '-response.json'), result)
    usage = result.get('usage', {})
    cost = (usage.get('input_tokens', 0) * config['input_rate_per_million'] + usage.get('output_tokens', 0) * config['output_rate_per_million']) / 1e6
    save(path / (q + '-receipt.json'), {'response_id': result.get('id'), 'returned_model': result.get('model'),
        'usage': usage, 'estimated_usd': cost, 'reserved_upper_usd': reservation['reserved_upper_usd'],
        'stop_reason': result.get('stop_reason'), 'finished_utc': now()})
    try:
        normalized = parse_response(row['question'], result)
        save(path / (q + '-normalized.json'), normalized)
        return {'id': q, 'state': 'VALIDATED_STRUCTURE_AND_LITERAL_EVIDENCE', 'estimated_usd': cost,
            'selected_ids': normalized['selected_ids']}
    except Exception as error:
        save(path / (q + '-parse-failure.json'), {'state': 'RESPONSE_RETAINED_NOT_RETRIED',
            'error_type': type(error).__name__, 'error': str(error)[:240]})
        return {'id': q, 'state': 'OUTPUT_VALIDATION_FAILED', 'estimated_usd': cost}


def run():
    frozen()
    if list((OUT / 'calls').glob('*-attempt.json')) or (OUT / 'run-start.json').exists():
        raise FileExistsError('Attempted requests cannot be silently sent again')
    config = read(CONFIG)
    rows = load('questions-and-development-expectations.json')['rows']
    bodies, reserve = load('requests.json'), load('reservation.json')
    save(OUT / 'run-start.json', {'started_utc': now(), 'frozen_sha256': sha(OUT / 'freeze.json'),
        'planned_calls': len(rows), 'reserved_upper_usd': reserve['reserved_upper_usd'], 'workers': 3, 'retries': 0})
    outcomes = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = {executor.submit(one_call, row, bodies[row['id']], reserve['reservations'][row['id']], config): row['id'] for row in rows}
        for future in as_completed(futures):
            outcome = future.result()
            outcomes.append(outcome)
            print(json.dumps(outcome, ensure_ascii=False), flush=True)
    estimated = sum(o.get('estimated_usd', 0) for o in outcomes)
    save(OUT / 'run.json', {'state': 'BOUNDED_REAL_LLM_SELECTION_RUN_FINISHED', 'finished_utc': now(),
        'outcomes': sorted(outcomes, key=lambda r: r['id']), 'attempts': len(outcomes),
        'estimated_received_usage_usd': estimated, 'reserved_upper_usd': reserve['reserved_upper_usd'],
        'delivery_uncertain_or_failed': sum(o['state'] in ('HTTP_FAILURE', 'UNKNOWN_DELIVERY') for o in outcomes),
        'fine_tuning': False, 'retrieval_performed': False, 'retries': 0})
    print('LLM_SELECTION_RUN_FINISHED', len(outcomes), 'estimated_usd', round(estimated, 6), flush=True)


def compute_review():
    rows = load('questions-and-development-expectations.json')['rows']
    checked = []
    normalized = {}
    for row in rows:
        q = row['id']
        path = OUT / 'calls' / (q + '-response.json')
        errors = []
        parsed = None
        if path.exists():
            try:
                parsed = parse_response(row['question'], json.loads(path.read_text(encoding='utf-8')))
            except Exception as error:
                errors.append('structure_or_literal_evidence:' + type(error).__name__)
        else:
            errors.append('no_received_response')
        if parsed is not None:
            normalized[q] = parsed
            if parsed['selected_ids'] not in [sorted(v) for v in row['allowed_selected']]:
                errors.append('selected_ids_outside_prespecified_development_expectation')
            if not set(row.get('require_pending', [])) <= set(parsed['pending_ids']):
                errors.append('required_pending_missing')
            if row.get('require_any_pending') and not parsed['pending_ids']:
                errors.append('no_pending_for_ambiguous_request')
            if row.get('require_unsupported') and not parsed['unsupported_work']:
                errors.append('unsupported_work_not_recorded')
            for text in row.get('constraint_quotes', []):
                if not any(text in e['quote'] for e in parsed['constraints']):
                    errors.append('query_constraint_missing:' + text)
        checked.append({'id': q, 'kind': row['kind'], 'allowed_selected': row['allowed_selected'],
            'actual_selected': parsed['selected_ids'] if parsed else None,
            'actual_pending': parsed['pending_ids'] if parsed else None,
            'output_valid': parsed is not None, 'development_contract_passed': not errors, 'errors': errors})
    repeats = []
    for row in rows:
        if row.get('repeat_of'):
            original, repeat = normalized.get(row['repeat_of']), normalized.get(row['id'])
            repeats.append({'id': row['id'], 'original': row['repeat_of'],
                'selection_stable': original is not None and repeat is not None and original['selected_ids'] == repeat['selected_ids'],
                'all_four_statuses_stable': original is not None and repeat is not None and
                    [(d['id'], d['status']) for d in original['decisions']] == [(d['id'], d['status']) for d in repeat['decisions']]})
    counts = {}
    for kind in ('SYNTHETIC_DEVELOPMENT', 'PREVIOUSLY_SEEN_REGRESSION', 'ORDER_DIAGNOSTIC_REPEAT'):
        group = [r for r in checked if r['kind'] == kind]
        counts[kind] = {'cases': len(group), 'output_valid': sum(r['output_valid'] for r in group),
            'development_contract_passed': sum(r['development_contract_passed'] for r in group)}
    ready = all(r['development_contract_passed'] for r in checked) and all(r['selection_stable'] for r in repeats)
    return {'state': 'DEVELOPMENT_CHECKS_PASSED_PROMPT_FROZEN' if ready else 'PROMPT_FROZEN_REVIEW_REQUIRED',
        'counts': counts, 'rows': checked, 'order_diagnostics': repeats,
        'independent_semantic_accuracy': False, 'human_gold': False, 'new_labels_for_retrieval': False,
        'retrieval_performance_compared': False, 'fine_tuning': False, 'test15_read': False,
        'limits': ['Assistant-authored development expectations', '24 unique questions; 4 order repeats are not independent samples',
            'Four historical questions previously inspected; not a fresh test',
            'Literal evidence checks do not certify semantic correctness', 'Single model and one selection per request; no final retrieval comparison']}, normalized


def review():
    frozen()
    result, normalized = compute_review()
    save(OUT / 'development-review.json', result)
    save(OUT / 'normalized-selections.json', normalized)
    save(OUT / 'final-freeze.json', {'state': result['state'], 'frozen_utc': now(),
        'initial_freeze_sha256': sha(OUT / 'freeze.json'),
        'source_sha256': load('freeze.json')['source_sha256'],
        'run_sha256': sha(OUT / 'run.json'), 'review_sha256': sha(OUT / 'development-review.json'),
        'normalized_sha256': sha(OUT / 'normalized-selections.json'), 'prompt_changes_after_outputs': 0,
        'retries': 0, 'retrieval_comparison_performed': False, 'human_gold': False})
    print(json.dumps({'state': result['state'], 'counts': result['counts'], 'order_diagnostics': result['order_diagnostics']}, ensure_ascii=False))


def verify():
    frozen()
    final = load('final-freeze.json')
    assert final['initial_freeze_sha256'] == sha(OUT / 'freeze.json')
    for filename, key in [('run.json', 'run_sha256'), ('development-review.json', 'review_sha256'), ('normalized-selections.json', 'normalized_sha256')]:
        assert sha(OUT / filename) == final[key]
    result, normalized = compute_review()
    assert result == load('development-review.json') and normalized == load('normalized-selections.json')
    rows = load('questions-and-development-expectations.json')['rows']
    config = read(CONFIG)
    catalog = read(config['source_catalog'])
    bodies = load('requests.json')
    reserve = load('reservation.json')
    assert reserve['reserved_upper_usd'] <= config['budget_usd']
    receipts, estimated = {}, 0
    for row in rows:
        q = row['id']
        assert bodies[q] == request_body(row['question'], config, catalog['cards'], reverse=row['reverse_cards'])
        path = OUT / 'calls' / (q + '-receipt.json')
        if path.exists():
            receipt = json.loads(path.read_text(encoding='utf-8'))
            assert receipt['estimated_usd'] <= reserve['reservations'][q]['reserved_upper_usd']
            receipts[q] = sha(path)
            estimated += receipt['estimated_usd']
        parsed_path = OUT / 'calls' / (q + '-normalized.json')
        if q in normalized:
            assert json.loads(parsed_path.read_text(encoding='utf-8')) == normalized[q]
    report = {'state': 'PASS_SAVED_API_RESPONSES_PROMPT_AND_REVIEW_REPLAY',
        'attempted_calls': len(list((OUT / 'calls').glob('*-attempt.json'))), 'received_receipts': len(receipts),
        'valid_outputs_replayed': len(normalized), 'estimated_usage_usd': estimated,
        'reserved_upper_usd': reserve['reserved_upper_usd'], 'receipt_sha256': receipts,
        'fine_tuning': False, 'retrieval_performance_compared': False, 'independent_gold': False,
        'prompt_changes_after_outputs': 0, 'test15_read': False}
    (OUT / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k:v for k,v in report.items() if k!='receipt_sha256'}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('phase', choices=['prepare', 'run', 'review', 'verify'])
    globals()[parser.parse_args().phase]()
