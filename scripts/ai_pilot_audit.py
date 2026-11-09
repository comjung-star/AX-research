"""Audit costs, literal evidence, source preservation and credential exclusion."""
import json
import os

from scripts.claude_blind_questions import OUT, save
from scripts.improvement_cycle import ROOT, read
from scripts.improvement_cycle10 import digest


def main():
    known = read('docs/independent-validation-20261108/ai_pilot/author_receipt.json')['estimated_usd']
    uncertain = 0.0
    attempts = 1
    for directory in ('blind_review', 'blind_review_v2', 'blind_review_429_recovery', 'runtime/api'):
        for path in (OUT / directory).glob('*_attempt.json'):
            attempts += 1
            receipt = path.with_name(path.name.replace('_attempt.json', '_receipt.json'))
            if receipt.exists():
                item = json.loads(receipt.read_text(encoding='utf-8'))
                known += item.get('estimated_usd', item.get('estimated_conservative_usd', 0))
            else:
                uncertain += json.loads(path.read_text(encoding='utf-8')).get('reserved_usd', 0)
    controls = OUT / 'synthetic_rater_controls/results.json'
    if controls.exists():
        result = json.loads(controls.read_text(encoding='utf-8'))['results']
        known += sum(row['estimated_usd'] for row in result.values())
        attempts += len(result)
    assert known + uncertain < 2
    freeze = read('docs/independent-validation-20261108/source_freeze.json')
    for path, checksum in freeze['sha256'].items():
        assert digest(ROOT / path) == checksum, path
    queries = {row['query_id']: row['text'] for row in map(json.loads, (OUT / 'questions.jsonl').read_text(encoding='utf-8').splitlines())}
    invalid_core, invalid_view = [], []
    for query, text in queries.items():
        for repeat in (1, 2, 3):
            core = json.loads((OUT / 'runtime/api/results' / f'X_{query}_r{repeat}.json').read_text(encoding='utf-8'))['data']['core']
            for field, value in core.items():
                if value is not None:
                    for quote in value['evidence']:
                        if quote not in text:
                            invalid_core.append({'query_id': query, 'repeat': repeat, 'field': field, 'quote': quote})
            views = json.loads((OUT / 'runtime/api/results' / f'E_{query}_r{repeat}.json').read_text(encoding='utf-8'))['data']['perspectives']
            for view in views:
                if view['status'] == 'PRESENT' and (not view['source_quote'] or view['source_quote'] not in text):
                    invalid_view.append({'query_id': query, 'repeat': repeat, 'slot': view['id'], 'quote': view['source_quote']})
    keys = [os.environ.get(name) for name in ('ANTHROPIC_API_KEY', 'OPENAI_API_KEY', 'GEMINI_API_KEY')]
    scanned = 0
    for path in OUT.rglob('*'):
        if path.suffix in ('.json', '.jsonl', '.md', '.csv'):
            content = path.read_text(encoding='utf-8-sig')
            assert not any(key and key in content for key in keys), 'Credential found in ' + str(path)
            scanned += 1
    result = {'state': 'PILOT_COST_PROVENANCE_AND_SECRET_AUDIT_COMPLETE', 'request_attempts_including_controls': attempts,
              'known_usage_estimate_usd': known, 'unknown_or_failed_request_reservations_usd': uncertain,
              'conservative_total_usd': known + uncertain, 'limit_usd': 2,
              'model_and_original_source_freeze_matches': True, 'secret_scanned_text_files': scanned,
              'invalid_core_literal_evidence': invalid_core, 'invalid_perspective_source_quotes': invalid_view,
              'invalid_evidence_repaired_or_regenerated': False, 'test15_opened': False,
              'interpretation': 'Literal evidence checks do not certify semantic fidelity or relevance truth.'}
    save(OUT / 'audit.json', result)
    print(json.dumps({key: value for key, value in result.items() if not key.startswith('invalid_')}))


if __name__ == '__main__':
    main()
