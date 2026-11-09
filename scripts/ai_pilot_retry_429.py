"""One explicit recovery of rejected429 requests only; never regenerate valid votes."""
import json
import time

from scripts.claude_blind_questions import OUT, save
from scripts.improvement_cycle import read
from scripts import ai_pilot_review_v2 as review


def main():
    execution = read('docs/independent-validation-20261108/ai_pilot/blind_review_v2/execution.json')
    failures = [row for row in execution['results'] if row.get('status') == 429]
    selected = {(row['provider'], row['query_id']) for row in failures}
    destination = OUT / 'blind_review_429_recovery'
    if destination.exists():
        raise FileExistsError(destination)
    queries = {row['query_id']: row for row in map(json.loads, (OUT / 'questions.jsonl').read_text(encoding='utf-8').splitlines())}
    registry = read('docs/dense-bm25-candidates-2026-10-27/case_registry.json')['cases']
    cases = [registry[case] for case in sorted(registry)]
    tasks = []
    for provider, query_id in sorted(selected):
        payload = {'query': queries[query_id]['text'], 'cases': [{'position': position, 'Problem': case['problem'], 'Task': case['task'], 'Context': case['context']} for position, case in enumerate(cases)]}
        reserve = ((len((review.PROMPT + json.dumps(payload, ensure_ascii=False)).encode()) + 2000) * review.RATES[provider][0] + 4096 * review.RATES[provider][1]) / 1e6
        tasks.append((provider, queries[query_id], cases, payload, reserve))
    old_upper = read('docs/independent-validation-20261108/ai_pilot/blind_review_v2/preregistration.json')['author_and_review_reserved_upper_usd']
    assert old_upper + sum(task[-1] for task in tasks) + .75 < 2
    destination.mkdir()
    save(destination / 'amendment.json', {'state': 'ONE_TECHNICAL_RECOVERY_BEFORE_MODEL_COMPARISON',
         'selection': sorted([list(pair) for pair in selected]), 'reason': 'KnownHTTP429rejection, no valid response exists',
         'valid_votes_regenerated': 0, 'maximum_additional_attempts': len(tasks),
         'whole_pilot_conservative_upper_including_runtime': old_upper + sum(task[-1] for task in tasks) + .75})
    review.REVIEW = destination
    results = []
    for task in tasks:
        results.append(review.run_one(*task))
        time.sleep(3)
    save(destination / 'execution.json', {'results': results, 'further_automatic_retries': 0})
    print(json.dumps({'requested': len(results), 'responses': sum(row['state'] == 'RECEIVED' for row in results)}))


if __name__ == '__main__':
    main()
