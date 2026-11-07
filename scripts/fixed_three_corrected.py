"""Preregistered clarification following source-only inspection of pilot outputs."""
from collections import defaultdict
from decimal import Decimal
import argparse
from pathlib import Path

from ax_research.heldout import jsonl, read, sha, write
from scripts import fixed_three_views as runner

OUT = runner.OUT
CORRECTED = OUT / 'corrected'
CLARIFICATION = """
Apply MISSING only if every relevant element for that slot is absent.
TECHNICAL is PRESENT if the source specifies any input, action, object or
output, even with no named tool or technology. OPERATIONS is PRESENT if any
handling step, recurring check, handoff, notification, or human decision is
stated, including a simple flow. Describe only those stated elements. If a
particular field is unknown, omit it from search text. Do not add generic
phrases such as 'technology is unspecified' to the search text. Preserve
priorities and conditional restrictions at their original strength.
"""


def request(kind, query_id, repeat):
    body = runner.request('fixed', query_id, repeat)
    body['instructions'] += CLARIFICATION
    return body


def prepare():
    CORRECTED.mkdir()
    write(CORRECTED / 'amendment.json', {
        'reason': 'Fixed pilot Q04 R1 marked technical absent despite explicit input, check and output. Q07 R1 also omitted technical. No performance data inspected.',
        'scope': 'All 30 fixed runs regenerated. B unchanged. Both original fixed pilot and corrected results retained.',
        'planned_additional_calls': 30, 'shared_budget_usd': 2,
        'request_template': request('corrected', 'NV20261102_01', 1),
        'adapter_sha256': sha(Path(__file__)),
    })


def generate():
    api = runner.api
    api.OUT, api.body, api.validate = OUT, request, runner.validate
    assert request('corrected', 'NV20261102_01', 1) == read(CORRECTED/'amendment.json')['request_template']
    try:
        for repeat in (1, 2, 3):
            for question in jsonl(runner.QUESTIONS):
                query = question['query_id']
                try:
                    api.call('corrected', query, repeat)
                except RuntimeError as error:
                    if str(error) != 'RECEIVED_BUT_INVALID_NO_AUTOMATIC_RETRY':
                        raise
                    api.call('corrected', query, repeat, 'format_retry')
    finally:
        records = []
        total = Decimal(0)
        upper = Decimal(0)
        for path in sorted((OUT/'api/attempts').glob('*.json'), key=lambda p: p.stat().st_mtime_ns):
            row = read(path)
            writes = row.get('usage', {}).get('input_tokens_details', {}).get('cache_write_tokens', 0)
            estimate = Decimal(row.get('standard_usage_usd', '0')) + Decimal(writes)*Decimal('.025')/1_000_000
            total += estimate
            upper += Decimal(row.get('conservative_usage_usd', row['reserved_usd']))
            records.append({**row, 'estimated_usd': str(estimate), 'cumulative_usd': str(total),
                            'cumulative_upper_usd': str(upper),
                            'valid': (OUT/'api/results'/(row['id']+'.json')).exists()})
        write(OUT/'api_ledger_final.json', {'calls': records, 'estimated_usd': str(total),
                                             'conservative_usd': str(upper), 'budget_usd': 2})


def load_paths():
    paths, sources, slots = [], {}, []
    for kind, offset in (('dynamic', 0), ('corrected', 3)):
        for repeat in (1, 2, 3):
            for q in jsonl(runner.QUESTIONS):
                query = q['query_id']
                stem = f'{kind}_{query}_r{repeat}'
                result = OUT/'api/results'/(stem+'.json')
                if not result.exists():
                    result = result.with_name(stem+'_format_retry.json')
                data = read(result)['data']
                runner.validate(kind, query, data)
                sources[result.relative_to(runner.ROOT).as_posix()] = sha(result)
                for i, view in enumerate(data['perspectives'], 1):
                    path = f'{stem}_{i}'
                    slots.append({'kind': kind, 'query_id': query, 'repeat': repeat, 'path_id': path, **view})
                    if view.get('status') != 'MISSING':
                        paths.append({'query_id': path, 'parent_query_id': query, 'repeat': repeat+offset,
                                      'text': view['title']+'\n'+view['description'], 'perspective': view})
    return paths, sources, slots


def infer(scratch):
    runner.OUT = CORRECTED
    runner.load_paths = load_paths
    runner.infer(scratch)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['prepare', 'generate', 'infer'])
    parser.add_argument('--scratch', type=Path)
    args = parser.parse_args()
    {'prepare': prepare, 'generate': generate, 'infer': lambda: infer(args.scratch)}[args.stage]()
