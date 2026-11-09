"""Generate frozen X/E runtime views only; no relevance inputs or scoring changes."""
import concurrent.futures
import json
import os
import threading
import time
import urllib.error
import urllib.request

from scripts.claude_blind_questions import OUT, save
from scripts.improvement_cycle import ROOT, read
from scripts import core_preservation_run as core

RUN = OUT / 'runtime'
LOCK = threading.Lock()
NEXT_REQUEST = 0.0
INTERVAL = 1.5


def request(kind, query, repeat):
    global NEXT_REQUEST, INTERVAL
    stem = f'{kind}_{query}_r{repeat}'
    body = core.body(kind, query, repeat)
    reserve = ((len(json.dumps(body, ensure_ascii=False).encode()) + 1000) * .125 + 1600 * .50) / 1e6
    save(RUN / 'api' / (stem + '_attempt.json'), {'state': 'RESERVED_NO_RETRY', 'reserved_usd': reserve})
    with LOCK:
        delay = max(0, NEXT_REQUEST - time.monotonic())
        NEXT_REQUEST = max(NEXT_REQUEST, time.monotonic()) + INTERVAL
    if delay:
        time.sleep(delay)
    headers = {'Authorization': 'Bearer ' + os.environ['OPENAI_API_KEY'], 'Content-Type': 'application/json'}
    payload = urllib.request.Request('https://api.openai.com/v1/responses', json.dumps(body).encode(), headers=headers)
    try:
        with urllib.request.urlopen(payload, timeout=120) as response:
            raw = json.load(response)
            rpm = response.headers.get('x-ratelimit-limit-requests', '')
            if rpm.isdigit():
                with LOCK:
                    INTERVAL = max(1., 60 / (int(rpm) * .6))
    except urllib.error.HTTPError as error:
        save(RUN / 'api' / (stem + '_failure.json'), {'state': 'HTTP_FAILURE_NO_RETRY', 'status': error.code})
        return False
    except Exception:
        save(RUN / 'api' / (stem + '_failure.json'), {'state': 'UNKNOWN_DELIVERY_NO_RETRY'})
        return False
    save(RUN / 'api' / (stem + '_response.json'), raw)
    usage = raw.get('usage', {})
    cost = (usage.get('input_tokens', 0) * .125 + usage.get('output_tokens', 0) * .5) / 1e6
    save(RUN / 'api' / (stem + '_receipt.json'), {'estimated_conservative_usd': cost, 'usage': usage, 'response_model': raw.get('model'),
                                               'status': raw.get('status'), 'request_interval_seconds': INTERVAL})
    try:
        assert raw.get('status') == 'completed'
        text = ''.join(part.get('text', '') for item in raw.get('output', []) for part in item.get('content', []) if part.get('type') == 'output_text')
        data = json.loads(text)
        core.validate(kind, query, data)
    except (AssertionError, ValueError, KeyError, TypeError):
        return False
    save(RUN / 'api/results' / (stem + '.json'), {'data': data, 'model': raw.get('model'), 'valid': True})
    print(json.dumps({'runtime_result': stem, 'usd_conservative': cost}), flush=True)
    return True


def job(item):
    query, repeat = item
    return {'query_id': query, 'repeat': repeat, 'valid': request('X', query, repeat) and request('E', query, repeat)}


def main():
    if RUN.exists():
        raise FileExistsError('Runtime generation already exists; do not replay attempts')
    RUN.mkdir()
    (RUN / 'api/results').mkdir(parents=True)
    core.OUT = RUN
    core.QUESTIONS = OUT / 'questions.jsonl'
    queries = [json.loads(line)['query_id'] for line in core.QUESTIONS.read_text(encoding='utf-8').splitlines()]
    jobs = [(query, repeat) for query in queries for repeat in (1, 2, 3)]
    save(RUN / 'preregistration.json', {'state': 'FROZEN_RUNTIME_X_E_GENERATION', 'query_count': 40, 'repeat_count': 3,
         'model': 'gpt-6-luna', 'prompt_source': 'unchanged scripts/core_preservation_prompts.py',
         'generation_only': True, 'case_corpus_or_grades_sent': False, 'maximum_successful_calls': 240,
         'per_request_upper_policy': 'UTF8bytes+1000 at0.125/MTok plus max1600output at0.5/MTok',
         'additional_generation_conservative_cap_usd': .75, 'overall_pilot_cap_usd': 2,
         'prices_checked': '2026-11-08', 'source': 'https://developers.openai.com/api/docs/models/gpt-6-luna'})
    first = job(jobs[0])
    if not first['valid']:
        raise RuntimeError('Runtime preflight failed; no remaining calls')
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        results = [first] + list(executor.map(job, jobs[1:]))
    receipts = [json.loads(path.read_text(encoding='utf-8')) for path in (RUN / 'api').glob('*_receipt.json')]
    upper = sum(row['estimated_conservative_usd'] for row in receipts)
    save(RUN / 'execution.json', {'results': results, 'complete_query_repeat_groups': sum(row['valid'] for row in results),
         'conservative_known_usage_usd': upper, 'receipt_count': len(receipts), 'relevance_inputs_used': False})
    print(json.dumps({'complete_groups': sum(row['valid'] for row in results), 'expected': 120, 'usd': upper}))


if __name__ == '__main__':
    main()
